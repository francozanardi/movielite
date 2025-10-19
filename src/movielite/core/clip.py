import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import Callable, Union, Tuple, Optional
import inspect

class Clip(ABC):
    """
    Base class for all media clips (video, image, audio, etc).

    A Clip has a start time, duration, and can be rendered at any given time.
    """

    def __init__(self, start: float, duration: float):
        """
        Initialize a Clip.

        Args:
            start: Start time in seconds
            duration: Duration in seconds
        """
        self._start = start
        self._duration = duration
        self._size: Tuple[int, int] = (0, 0)
        self._position: Callable[[float], Tuple[int, int]] = lambda t: (0, 0)
        self._opacity: Callable[[float], float] = lambda t: 1
        self._scale: Callable[[float], float] = lambda t: 1
        self._frame_transform: Optional[Callable[[np.ndarray, float], np.ndarray]] = None

    def set_position(self, value: Union[Callable[[float], Tuple[int, int]], Tuple[int, int]]) -> 'Clip':
        """
        Set the position of the clip.

        Args:
            value: Either a tuple (x, y) or a function that takes time and returns (x, y)

        Returns:
            Self for chaining
        """
        self._position = self._save_as_function(value)
        return self

    def set_opacity(self, value: Union[Callable[[float], float], float]) -> 'Clip':
        """
        Set the opacity of the clip.

        Args:
            value: Either a float (0-1) or a function that takes time and returns opacity

        Returns:
            Self for chaining
        """
        self._opacity = self._save_as_function(value)
        return self

    def set_scale(self, value: Union[Callable[[float], float], float]) -> 'Clip':
        """
        Set the scale of the clip.

        Args:
            value: Either a float or a function that takes time and returns scale

        Returns:
            Self for chaining
        """
        self._scale = self._save_as_function(value)
        return self

    def set_size(self, width: Optional[int] = None, height: Optional[int] = None) -> 'Clip':
        """
        Set the size of the clip, maintaining aspect ratio if only one dimension is provided.

        Args:
            width: Target width (optional)
            height: Target height (optional)

        Returns:
            Self for chaining
        """
        if width is None and height is None:
            raise ValueError(f"Either width ({width}) or height ({height}) must contain a value")

        if width is None:
            if height <= 0:
                raise ValueError(f"Invalid combination of widthxheight: {width}x{height}")
            new_w = int((height / self._size[1]) * self._size[0])
            new_h = int(height)
        elif height is None:
            if width <= 0:
                raise ValueError(f"Invalid combination of widthxheight: {width}x{height}")
            new_w = int(width)
            new_h = int((width / self._size[0]) * self._size[1])
        else:
            new_w = int(width)
            new_h = int(height)

        self._size = (new_w, new_h)
        return self

    def set_duration(self, duration: float) -> 'Clip':
        """
        Set the duration of the clip.

        Args:
            duration: New duration in seconds

        Returns:
            Self for chaining
        """
        self._duration = duration
        return self

    def transform_frame(self, callback: Callable[[np.ndarray, float], np.ndarray]) -> 'Clip':
        """
        Apply a custom transformation to each frame at render time.

        The callback receives the frame (np.ndarray) and relative time (float),
        and should return the transformed frame.

        Args:
            callback: Function that takes (frame, time) and returns transformed frame

        Returns:
            Self for chaining

        Example:
            >>> def make_sepia(frame, t):
            >>>     # Apply sepia filter
            >>>     return sepia_filter(frame)
            >>> clip.transform_frame(make_sepia)
        """
        self._frame_transform = callback
        return self

    def _save_as_function(self, value: Union[Callable, float, Tuple[int, int]]) -> Callable:
        """Convert static values to time-based functions"""
        if inspect.isfunction(value):
            return value
        return lambda t, v=value: v

    @property
    def position(self):
        return self._position

    @property
    def opacity(self):
        return self._opacity

    @property
    def scale(self):
        return self._scale

    @property
    def size(self):
        return self._size

    @property
    def start(self):
        return self._start

    @property
    def duration(self):
        return self._duration

    @property
    def end(self):
        return self.start + self.duration

    @abstractmethod
    def get_frame(self, t_rel: float) -> np.ndarray:
        """
        Get the frame at a relative time within the clip.

        Args:
            t_rel: Relative time within the clip (0 to duration)

        Returns:
            Frame as numpy array
        """
        pass

    def render(self, bg: np.ndarray, t_global: float) -> np.ndarray:
        """
        Render this clip onto a background at a given global time.

        Args:
            bg: Background frame (BGR or BGRA)
            t_global: Global time in seconds

        Returns:
            Background with this clip rendered on top
        """
        from .logger import get_logger

        t_rel = (t_global - self._start)

        # Debug: Log first few render calls
        if t_global < 0.1:
            get_logger().debug(f"{self.__class__.__name__}.render: t_global={t_global:.3f}, start={self._start:.3f}, t_rel={t_rel:.3f}, duration={self._duration:.3f}, in_range={0 <= t_rel < self._duration}")

        if not (0 <= t_rel < self._duration):
            return bg

        frame = self.get_frame(t_rel)

        # Apply custom frame transformation if set
        if self._frame_transform is not None:
            frame = self._frame_transform(frame, t_rel)

        x, y = self.position(t_rel)
        x, y = int(x), int(y)
        s = self.scale(t_rel)
        alpha_val = self.opacity(t_rel)

        # Scale frame
        interpolation_method = cv2.INTER_AREA if s < 1.0 else cv2.INTER_CUBIC
        scaled_w, scaled_h = int(self._size[0] * s), int(self._size[1] * s)
        frame = cv2.resize(frame, (scaled_w, scaled_h), interpolation=interpolation_method)
        frame = np.clip(frame, 0.0, 255.0)

        # Ensure BGRA format
        if frame.shape[2] == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            # cv2.cvtColor sets alpha to 0, we need to set it to 255 (opaque)
            frame[:, :, 3] = 255.0

        # Apply opacity
        frame[:, :, 3] = frame[:, :, 3] * alpha_val

        H, W = bg.shape[:2]
        h, w = frame.shape[:2]

        # Calculate positions
        y1_bg = max(y, 0)
        x1_bg = max(x, 0)
        y2_bg = min(y + h, H)
        x2_bg = min(x + w, W)

        # Check if frame is outside background
        if y1_bg >= y2_bg or x1_bg >= x2_bg:
            return bg

        # Frame coordinates
        y1_fr = y1_bg - y
        x1_fr = x1_bg - x
        y2_fr = y2_bg - y
        x2_fr = x2_bg - x

        # Alpha blending
        roi = bg[y1_bg:y2_bg, x1_bg:x2_bg]
        sub_fr = frame[y1_fr:y2_fr, x1_fr:x2_fr]
        frame_alpha = sub_fr[..., 3:4] / 255.0
        roi_float = roi.astype(np.float32) if roi.dtype != np.float32 else roi

        if bg.shape[2] == 3:
            # Background is BGR format
            blended_roi = sub_fr[..., :3] * frame_alpha + roi_float * (1.0 - frame_alpha)
        else:
            # Background is BGRA format
            bg_alpha = roi[..., 3:4] / 255.0
            final_alpha = frame_alpha + bg_alpha * (1.0 - frame_alpha)

            blended_rgb = (sub_fr[..., :3] * frame_alpha + roi_float[..., :3] * bg_alpha * (1.0 - frame_alpha)) / np.clip(final_alpha, 1e-6, 1.0)
            blended_alpha = final_alpha * 255.0
            blended_roi = np.concatenate([blended_rgb, blended_alpha], axis=-1)

        final_roi = np.clip(blended_roi, 0, 255)
        bg[y1_bg:y2_bg, x1_bg:x2_bg] = final_roi.astype(bg.dtype)

        return bg
