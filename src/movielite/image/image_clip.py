import cv2
import numpy as np
from typing import Union
from ..core import GraphicClip

class ImageClip(GraphicClip):
    """
    An image clip that displays a static image for a given duration.

    Can be loaded from a file path or from a numpy array.
    """

    def __init__(self, source: Union[str, np.ndarray], start: float = 0, duration: float = 5.0):
        """
        Create an image clip.

        Args:
            source: Either a file path (str) or a numpy array (RGBA or RGB)
            start: Start time in the composition (seconds)
            duration: How long to display the image (seconds)
        """
        super().__init__(start, duration)

        if isinstance(source, str):
            img = cv2.imread(source, cv2.IMREAD_UNCHANGED)  # BGR or BGRA from OpenCV
            if img is None:
                raise FileNotFoundError(f"Image not found: {source}")
        else:
            img = source.copy()

            if img.ndim != 3 or img.shape[2] not in (3, 4):
                raise ValueError("source numpy array must have shape (h, w, 3) or (h, w, 4)")

            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        if img.shape[2] == 4:
            alpha = img[:, :, 3]
            if (alpha == 255).all():
                # Fully opaque, drop alpha channel to convert to BGR (it will save us memory)
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        self._image = img.astype(np.uint8)
        self._size = (self._image.shape[1], self._image.shape[0])
        self._original_image = self._image  # Keep original for potential re-resizing

    def get_frame(self, t_rel: float) -> np.ndarray:
        """Get the image frame (same for all times)"""
        return self._image

    def _apply_resize(self, frame: np.ndarray) -> np.ndarray:
        interpolation = cv2.INTER_AREA if (self._target_size[0] < self._size[0]) else cv2.INTER_CUBIC
        self._image = cv2.resize(self._original_image, self._target_size, interpolation=interpolation)
        self._size = self._target_size
        self._target_size = None
        return self._image

    def _convert_to_mask(self, frame: np.ndarray) -> np.ndarray:
        """Convert image frame to 2D mask (0-255 uint8)"""
        if frame.shape[2] == 4:
            # Use alpha channel
            mask = frame[:, :, 3]
        else:
            # Convert to grayscale
            mask = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return mask

    @classmethod
    def from_color(cls, color: tuple, size: tuple, start: float = 0, duration: float = 5.0) -> 'ImageClip':
        """
        Create a solid color image clip.

        Args:
            color: RGB or RGBA tuple (0-255)
            size: (width, height)
            start: Start time in seconds
            duration: Duration in seconds

        Returns:
            ImageClip instance
        """
        if len(color) == 3:
            color = (*color, 255)

        img = np.full((size[1], size[0], 4), color, dtype=np.uint8)
        return cls(img, start, duration)
