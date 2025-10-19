import cv2
import numpy as np
import os
from typing import Optional
from .clip import Clip
from .logger import get_logger

class VideoClip(Clip):
    """
    A lightweight video clip that doesn't load frames.

    This class only stores metadata (path, fps, size, duration) and is designed
    for fast video manipulation using FFmpeg filters without pixel-level processing.

    For transformations that require frame-level processing (custom effects, filters),
    use ProcessedVideoClip instead.
    """

    def __init__(self, path: str, start: float = 0, duration: Optional[float] = None, offset: float = 0):
        """
        Load a video clip (metadata only).

        Args:
            path: Path to the video file
            start: Start time in the composition (seconds)
            duration: Duration to use from the video (if None, uses full video duration)
            offset: Start offset within the video file (seconds)
        """
        ext = os.path.splitext(path)[1].lower()
        if ext not in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
            raise ValueError(f"Unsupported video format: {ext}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Video file not found: {path}")

        self._path = path
        self._offset = offset

        # Load metadata first to get video properties
        self._load_metadata(path)

        # Determine actual duration
        video_duration = self._total_frames / self._fps
        if duration is None:
            duration = video_duration - offset
        else:
            duration = min(duration, video_duration - offset)

        # Call parent constructor - this will reset self._size to (0, 0)
        super().__init__(start, duration)

        # Re-set the size after calling super().__init__()
        # (Clip.__init__ sets _size to (0, 0), so we need to restore it)
        self._size = (self._video_width, self._video_height)

    def get_frame(self, t_rel: float) -> np.ndarray:
        """
        VideoClip does not support direct frame access.

        Use ProcessedVideoClip.from_video_clip() to convert this clip
        if you need frame-level processing.
        """
        raise NotImplementedError(
            "VideoClip does not load frames. Use ProcessedVideoClip for frame-level processing."
        )

    def subclip(self, start: float, end: float) -> 'VideoClip':
        """
        Extract a subclip from this video.

        Args:
            start: Start time within this clip (seconds)
            end: End time within this clip (seconds)

        Returns:
            New VideoClip instance
        """
        if start < 0 or end > self.duration or start >= end:
            raise ValueError(f"Invalid subclip range: ({start}, {end}) for clip duration {self.duration}")

        # Create a new instance with adjusted timing
        new_clip = VideoClip.__new__(VideoClip)
        new_clip._path = self._path
        new_clip._fps = self._fps
        new_clip._video_width = self._video_width
        new_clip._video_height = self._video_height
        new_clip._size = self._size
        new_clip._total_frames = self._total_frames
        new_clip._offset = self._offset + start
        new_clip._start = 0
        new_clip._duration = end - start
        new_clip._position = self._position
        new_clip._opacity = self._opacity
        new_clip._scale = self._scale
        new_clip._frame_transform = self._frame_transform

        return new_clip

    def transform_frame(self, callback):
        """
        VideoClip does not support frame transformations.

        Use ProcessedVideoClip.from_video_clip() to convert this clip
        if you need to apply custom frame transformations.
        """
        raise NotImplementedError(
            "VideoClip does not support frame transformations. Use ProcessedVideoClip for custom transformations."
        )

    def set_position(self, x, y=None):
        """VideoClip does not support position changes. Use ProcessedVideoClip."""
        raise NotImplementedError(
            "VideoClip does not support set_position(). Use ProcessedVideoClip for positioning."
        )

    def set_opacity(self, opacity):
        """VideoClip does not support opacity changes. Use ProcessedVideoClip."""
        raise NotImplementedError(
            "VideoClip does not support set_opacity(). Use ProcessedVideoClip for opacity changes."
        )

    def set_scale(self, scale):
        """VideoClip does not support scale changes. Use ProcessedVideoClip."""
        raise NotImplementedError(
            "VideoClip does not support set_scale(). Use ProcessedVideoClip for scaling."
        )

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

        # Store in separate variables to avoid being overwritten by Clip.__init__
        self._video_width = w
        self._video_height = h

        get_logger().debug(f"VideoClip loaded (metadata only): {path}, size=({w}, {h}), fps={self._fps}, frames={self._total_frames}")
        cap.release()

    @property
    def fps(self):
        """Get the frames per second of this video"""
        return self._fps
