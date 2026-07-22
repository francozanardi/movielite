import cv2
import numpy as np
from typing import Optional

from .base import VideoReader
from ...logger import get_logger


class Cv2Reader(VideoReader):
    """BGR reader backed by cv2.VideoCapture.

    Fast for codecs the local OpenCV build supports (typically H.264, MPEG-4,
    VP8/VP9). Silently returns empty frames for codecs it can't decode -
    consumers should call probe() before trusting this reader.
    """

    def __init__(self, path: str):
        self._path = path
        cap = cv2.VideoCapture(self._path)
        if not cap.isOpened():
            raise RuntimeError(f"cv2 could not open {path}")

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = cap.get(cv2.CAP_PROP_FPS)
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self._fps <= 0 or w <= 0 or h <= 0 or self._total_frames <= 0:
            cap.release()
            raise RuntimeError(f"Could not read valid properties from video: {path}")

        self._size = (w, h)
        cap.release()

        self._cap: Optional[cv2.VideoCapture] = None
        self._last_frame_idx = -1
        self._last_frame: Optional[np.ndarray] = None

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
        return 3

    def probe(self) -> bool:
        """Attempt to decode frame 0. On success, cache it for reuse.

        This is how open_reader() decides whether cv2 can handle the codec:
        some codecs (AV1 without HW support, HEVC on stripped OpenCV builds)
        return ret=False from cap.read() even though isOpened() said True.
        """
        if self._cap is None:
            self._cap = cv2.VideoCapture(self._path)
        ret, frame = self._cap.read()
        if ret and frame is not None:
            self._last_frame_idx = 0
            self._last_frame = frame
            return True
        return False

    def get_frame(self, frame_idx: int) -> np.ndarray:
        frame_idx = max(0, min(frame_idx, self._total_frames - 1))

        if self._cap is None:
            self._cap = cv2.VideoCapture(self._path)
            self._last_frame_idx = -1

        if frame_idx == self._last_frame_idx and self._last_frame is not None:
            return self._last_frame

        # Backward jump or a long forward jump: seek by index (cheap in cv2).
        if frame_idx < self._last_frame_idx or frame_idx - self._last_frame_idx > 5:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self._cap.read()
            if not ret:
                get_logger().warning(f"Failed to read frame {frame_idx} from {self._path}")
                frame = np.zeros((self._size[1], self._size[0], 3), dtype=np.uint8)
            self._last_frame_idx = frame_idx
            self._last_frame = frame
            return frame

        # Short forward jump: read sequentially, cheaper than seek+decode-keyframe.
        current = self._last_frame_idx
        frame = self._last_frame
        while current < frame_idx:
            ret, frame = self._cap.read()
            if not ret:
                get_logger().warning(f"Failed to read frame {frame_idx} from {self._path}")
                frame = np.zeros((self._size[1], self._size[0], 3), dtype=np.uint8)
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
