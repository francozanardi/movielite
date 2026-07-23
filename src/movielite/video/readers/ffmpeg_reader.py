import subprocess
import numpy as np
from typing import Literal, Optional

from .base import VideoReader
from ...logger import get_logger

PixFmt = Literal["bgr24", "bgra"]


class FfmpegReader(VideoReader):
    """BGR or BGRA reader backed by an ffmpeg subprocess piping rawvideo.

    Handles any codec the local ffmpeg supports (AV1, HEVC, VP9, ...). Costs:
      - Constant ~90MB of RSS from the subprocess (libavcodec + buffers).
      - Any backward jump or long forward jump reopens the subprocess with -ss,
        which is ~90ms of startup per reopen.

    Metadata is read with ffprobe. Frame counts come from the container
    (nb_frames) and are trusted; if the container lies, get_frame() will
    still work but total_frames may be slightly off.
    """

    def __init__(self, path: str, pix_fmt: PixFmt = "bgr24"):
        self._path = path
        self._pix_fmt = pix_fmt
        self._channels = 4 if pix_fmt == "bgra" else 3
        self._load_metadata()
        self._proc: Optional[subprocess.Popen] = None
        self._last_frame_idx = -1
        self._last_frame: Optional[np.ndarray] = None

    def _load_metadata(self) -> None:
        # We prefer nb_frames from the container (fast). Fallback to duration*fps
        # if the container doesn't expose it - avoids the very expensive
        # -count_frames path that AlphaVideoClip used to do unconditionally.
        #
        # Output format is key=value (default), not csv=p=0: ffprobe's csv output
        # reorders fields (alphabetically-ish), so positional parsing is brittle.
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,nb_frames,duration",
            "-of", "default=noprint_wrappers=1",
            self._path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        meta: dict[str, str] = {}
        for line in result.stdout.strip().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k.strip()] = v.strip()

        w = int(meta["width"])
        h = int(meta["height"])
        num, den = meta["r_frame_rate"].split("/")
        self._fps = float(num) / float(den)

        nb_frames_str = meta.get("nb_frames", "")
        duration_str = meta.get("duration", "")

        if nb_frames_str and nb_frames_str != "N/A":
            self._total_frames = int(nb_frames_str)
        elif duration_str and duration_str != "N/A":
            self._total_frames = int(float(duration_str) * self._fps)
        else:
            raise RuntimeError(f"Could not determine frame count for video: {self._path}")

        if self._fps <= 0 or w <= 0 or h <= 0 or self._total_frames <= 0:
            raise RuntimeError(f"Invalid video properties for: {self._path}")

        self._size = (w, h)

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def total_frames(self) -> int:
        return self._total_frames

    @property
    def channels(self) -> int:
        return self._channels

    def _open_at(self, start_frame: int) -> None:
        self._close_proc()
        start_time = start_frame / self._fps
        cmd = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", self._path,
            "-f", "rawvideo",
            "-pix_fmt", self._pix_fmt,
            "-vsync", "0",
            "-",
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**8,
        )
        self._last_frame_idx = start_frame - 1
        get_logger().debug(f"FfmpegReader: opened pipe at frame {start_frame} for {self._path}")

    def _read_next(self) -> np.ndarray:
        assert self._proc is not None
        size = self._size[0] * self._size[1] * self._channels
        raw = self._proc.stdout.read(size)
        if len(raw) < size:
            get_logger().warning(f"Failed to read frame from ffmpeg pipe for {self._path}")
            return np.zeros((self._size[1], self._size[0], self._channels), dtype=np.uint8)
        return np.frombuffer(raw, dtype=np.uint8).reshape((self._size[1], self._size[0], self._channels))

    def get_frame(self, frame_idx: int) -> np.ndarray:
        frame_idx = max(0, min(frame_idx, self._total_frames - 1))

        if frame_idx == self._last_frame_idx and self._last_frame is not None:
            return self._last_frame

        # Reopen only on backward jumps or long forward jumps. Short forward
        # jumps read sequentially from the running pipe - much cheaper than
        # reopening the subprocess.
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
