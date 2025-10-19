from .media_element import MediaElement
import cv2
import numpy as np
import os
import subprocess
import re

class VideoElement(MediaElement):

    def __init__(self, path: str, start: float, duration: float):
        super().__init__(start, duration)
        ext = os.path.splitext(path)[1].lower()
        if ext not in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            raise ValueError(f"Unsupported video format: {ext}")

        self._load_metadata(path)
        self._load_frames_with_ffmpeg(path)

    def get_frame(self, t_rel: float) -> np.ndarray:
        idx = int(t_rel * self._fps)
        idx = max(0, min(idx, self._num_frames - 1))
        return self._frames[idx].copy()

    def _load_metadata(self, path: str) -> None:
        cmd = ["ffmpeg", "-hide_banner", "-i", path]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr = proc.stderr

        res_match = re.search(r",\s*(\d{1,5})x(\d{1,5})[,\s]", stderr)
        if not res_match:
            raise RuntimeError(f"Unable to get width/height from ffmpeg stderr:\n{stderr}")
        width, height = map(int, res_match.groups())
        self._size = (width, height)

        fps_match = re.search(r"(\d+(?:\.\d+)?)\s+fps", stderr)
        if not fps_match:
            raise RuntimeError(f"Unable to get fps from ffmpeg stderr:\n{stderr}")
        self._fps = float(fps_match.group(1))

            
    def _load_frames_with_ffmpeg(self, path: str):
        w, h = self._size
        cmd = [
            "ffmpeg", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgba",
            "-vf", f"scale={w}:{h}", "-hide_banner", "-loglevel", "error", "pipe:1"
        ]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            bufsize=10**8
        )

        frame_size = w * h * 4
        frames = []
        while True:
            raw = proc.stdout.read(frame_size)
            if len(raw) < frame_size:
                break
            arr = np.frombuffer(raw, dtype=np.uint8)
            arr = arr.reshape((h, w, 4))
            arr = arr.astype(np.float32)
            arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
            frames.append(arr)

        proc.wait()
        self._frames = frames
        self._num_frames = len(frames)
