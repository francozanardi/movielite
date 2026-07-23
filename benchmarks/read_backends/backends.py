"""Two frame-reader backends with the same API, ready to benchmark head-to-head.

Both replicate what movielite does today so the numbers are comparable:

    Cv2Backend    - mirrors VideoClip.get_frame (cv2.VideoCapture, seek by frame
                    index, cached last frame, jumps <=5 read forward).
    FfmpegBackend - mirrors AlphaVideoClip.get_frame (ffprobe for metadata,
                    ffmpeg subprocess piping rawvideo bgr24, seek by -ss reopen).

Output format is BGR24 for both (3 bytes/pixel), matching VideoClip (not the
BGRA path used by AlphaVideoClip). This isolates the decoder change from the
alpha-channel cost.

The API is (Backend).get_frame(frame_idx) -> np.ndarray, plus .close().
Metadata is loaded eagerly in __init__.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np


class Cv2Backend:
    """OpenCV VideoCapture backend, same logic as movielite's VideoClip."""

    name = "cv2"

    def __init__(self, path: str | Path):
        self._path = str(path)
        cap = cv2.VideoCapture(self._path)
        if not cap.isOpened():
            raise RuntimeError(f"cv2 could not open {path}")
        self._w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = cap.get(cv2.CAP_PROP_FPS)
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        self._cap: cv2.VideoCapture | None = None
        self._last_frame_idx = -1
        self._last_frame: np.ndarray | None = None

    @property
    def size(self) -> tuple[int, int]:
        return (self._w, self._h)

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def total_frames(self) -> int:
        return self._total_frames

    def get_frame(self, frame_idx: int) -> np.ndarray:
        frame_idx = max(0, min(frame_idx, self._total_frames - 1))

        if self._cap is None:
            self._cap = cv2.VideoCapture(self._path)
            self._last_frame_idx = -1

        if frame_idx == self._last_frame_idx and self._last_frame is not None:
            return self._last_frame

        if frame_idx < self._last_frame_idx or frame_idx - self._last_frame_idx > 5:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self._cap.read()
            if not ret:
                frame = np.zeros((self._h, self._w, 3), dtype=np.uint8)
            self._last_frame_idx = frame_idx
            self._last_frame = frame
            return frame

        current = self._last_frame_idx
        frame = self._last_frame
        while current < frame_idx:
            ret, frame = self._cap.read()
            if not ret:
                frame = np.zeros((self._h, self._w, 3), dtype=np.uint8)
            current += 1

        self._last_frame_idx = current
        self._last_frame = frame
        return frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        self._last_frame = None
        self._last_frame_idx = -1


class FfmpegBackend:
    """FFmpeg subprocess backend, same logic as AlphaVideoClip (but BGR24)."""

    name = "ffmpeg"

    def __init__(self, path: str | Path):
        self._path = str(path)
        self._load_metadata()
        self._proc: subprocess.Popen | None = None
        self._last_frame_idx = -1
        self._last_frame: np.ndarray | None = None

    def _load_metadata(self) -> None:
        # Single ffprobe call: width, height, r_frame_rate, nb_frames.
        # nb_frames is trusted here (no -count_frames) because our fixtures
        # are freshly encoded and container-correct. Real movielite might
        # need -count_frames as a fallback, which is significantly slower.
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
            "-of", "csv=p=0",
            self._path,
        ]
        parts = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip().split(",")
        self._w = int(parts[0])
        self._h = int(parts[1])
        num, den = parts[2].split("/")
        self._fps = float(num) / float(den)
        self._total_frames = int(parts[3])

    @property
    def size(self) -> tuple[int, int]:
        return (self._w, self._h)

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def total_frames(self) -> int:
        return self._total_frames

    def _open_at(self, start_frame: int) -> None:
        self._close_proc()
        start_time = start_frame / self._fps
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", self._path,
            "-f", "rawvideo",
            "-pix_fmt", "bgr24",
            "-vsync", "0",
            "-",
        ]
        self._proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8,
        )
        self._last_frame_idx = start_frame - 1

    def _read_next(self) -> np.ndarray:
        assert self._proc is not None
        size = self._w * self._h * 3
        raw = self._proc.stdout.read(size)
        if len(raw) < size:
            return np.zeros((self._h, self._w, 3), dtype=np.uint8)
        return np.frombuffer(raw, dtype=np.uint8).reshape((self._h, self._w, 3))

    def get_frame(self, frame_idx: int) -> np.ndarray:
        frame_idx = max(0, min(frame_idx, self._total_frames - 1))

        if frame_idx == self._last_frame_idx and self._last_frame is not None:
            return self._last_frame

        # Reopen on backward jump or a long forward jump.
        needs_seek = frame_idx < self._last_frame_idx or frame_idx - self._last_frame_idx > 10
        if self._proc is None or needs_seek:
            self._open_at(frame_idx)

        current = self._last_frame_idx
        frame = self._last_frame
        while current < frame_idx:
            frame = self._read_next()
            current += 1

        self._last_frame_idx = current
        self._last_frame = frame
        return frame

    def _close_proc(self) -> None:
        if self._proc is not None:
            try:
                self._proc.stdout.close()
            except Exception:
                pass
            self._proc.terminate()
            self._proc.wait()
            self._proc = None

    def close(self) -> None:
        self._close_proc()
        self._last_frame = None
        self._last_frame_idx = -1


BACKENDS = {"cv2": Cv2Backend, "ffmpeg": FfmpegBackend}
