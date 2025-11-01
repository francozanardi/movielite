import cv2
import numpy as np
import os
from typing import Optional
from .clip import Clip
from .logger import get_logger

# TODO: it doesn't support transparency, we must add a new VideoClip subclass that supports alpha channel
class VideoClip(Clip):
    """
    A video clip that loads and processes frames.
    """

    def __init__(self, path: str, start: float = 0, duration: Optional[float] = None, offset: float = 0):
        """
        Load a video clip for frame-level processing.

        Args:
            path: Path to the video file
            start: Start time in the composition (seconds)
            duration: Duration to use from the video (if None, uses full video duration)
            offset: Start offset within the video file (seconds)
        """
        super().__init__(start, duration)

        ext = os.path.splitext(path)[1].lower()
        if ext not in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            raise ValueError(f"Unsupported video format: {ext}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Video file not found: {path}")

        self._path = path
        self._offset = offset

        self._load_metadata(path)

        # Determine actual duration
        video_duration = self._total_frames / self._fps
        if duration is None:
            duration = video_duration - offset
        else:
            duration = min(duration, video_duration - offset)

        self._cap = None
        self._current_frame_idx = -1
        self._last_frame = None

    def get_frame(self, t_rel: float) -> np.ndarray:
        """Get frame at relative time within this clip"""
        actual_time = t_rel + self._offset
        frame_idx = int(actual_time * self._fps)
        frame_idx = max(0, min(frame_idx, self._total_frames - 1))

        # Open capture if not already open
        if self._cap is None:
            self._cap = cv2.VideoCapture(self._path)
            self._current_frame_idx = -1
            get_logger().debug(f"ProcessedVideoClip: Opened video capture for {self._path}")

        if frame_idx == self._current_frame_idx and self._last_frame is not None:
            return self._last_frame
        elif frame_idx == self._current_frame_idx + 1:
            # Read next frame sequentially
            ret, frame = self._cap.read()
            if not ret:
                get_logger().warning(f"Failed to read frame {frame_idx} from {self._path}")
                return np.zeros((self._size[1], self._size[0], 3), dtype=np.uint8)
            self._current_frame_idx = frame_idx
        elif frame_idx > self._current_frame_idx and frame_idx - self._current_frame_idx <= 5:
            # Skip a few frames (still relatively fast)
            for _ in range(frame_idx - self._current_frame_idx):
                ret, frame = self._cap.read()
                if not ret:
                    get_logger().warning(f"Failed to read frame {frame_idx} from {self._path}")
                    return np.zeros((self._size[1], self._size[0], 3), dtype=np.uint8)
            self._current_frame_idx = frame_idx
        else:
            # Need to seek (slower, but necessary for random access)
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = self._cap.read()
            if not ret:
                get_logger().warning(f"Failed to read frame {frame_idx} from {self._path}")
                return np.zeros((self._size[1], self._size[0], 3), dtype=np.uint8)
            self._current_frame_idx = frame_idx

        self._last_frame = frame
        return frame

    def _apply_resize(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame (happens every frame for videos)"""
        interpolation = cv2.INTER_AREA if (self._target_size[0] < frame.shape[1]) else cv2.INTER_CUBIC
        return cv2.resize(frame, self._target_size, interpolation=interpolation)

    def close(self):
        """Close the video file"""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            self._current_frame_idx = -1
            self._last_frame = None

    def __del__(self):
        """Ensure video file is closed when object is destroyed"""
        self.close()

    def subclip(self, start: float, end: float) -> 'VideoClip':
        """
        Extract a subclip from this video.

        Args:
            start: Start time within this clip (seconds)
            end: End time within this clip (seconds)

        Returns:
            New ProcessedVideoClip instance
        """
        if start < 0 or end > self.duration or start >= end:
            raise ValueError(f"Invalid subclip range: ({start}, {end}) for clip duration {self.duration}")

        # Create a new instance with adjusted timing
        new_clip = VideoClip.__new__(VideoClip)
        new_clip._path = self._path
        new_clip._fps = self._fps
        new_clip._size = self._size
        new_clip._total_frames = self._total_frames
        new_clip._offset = self._offset + start
        new_clip._start = 0
        new_clip._duration = end - start
        new_clip._position = self._position
        new_clip._opacity = self._opacity
        new_clip._scale = self._scale
        new_clip._target_size = self._target_size
        new_clip._frame_transforms = self._frame_transforms.copy()
        new_clip._has_any_transform = self._has_any_transform
        new_clip._cap = None
        new_clip._current_frame_idx = -1
        new_clip._last_frame = None

        return new_clip

    def _load_metadata(self, path: str) -> None:
        """Load video metadata using cv2.VideoCapture"""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video file: {path}")

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = cap.get(cv2.CAP_PROP_FPS)
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self._fps <= 0 or w <= 0 or h <= 0 or self._total_frames <= 0:
            cap.release()
            raise RuntimeError(f"Could not read valid properties from video: {path}")

        self._size = (w, h)

        get_logger().debug(f"ProcessedVideoClip loaded: {path}, size=({w}, {h}), fps={self._fps}, frames={self._total_frames}")
        cap.release()

    @property
    def fps(self):
        """Get the frames per second of this video"""
        return self._fps
