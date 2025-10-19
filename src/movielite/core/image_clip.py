import cv2
import numpy as np
from typing import Union
from .clip import Clip

class ImageClip(Clip):
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
            img = cv2.imread(source, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise FileNotFoundError(f"Image not found: {source}")
            if img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        else:
            if source.shape[2] == 4:
                img = cv2.cvtColor(source, cv2.COLOR_RGBA2BGRA)
            else:
                img = cv2.cvtColor(source, cv2.COLOR_RGB2BGRA)

        self._image = img.astype(np.float32)
        self._size = self._image.shape[1], self._image.shape[0]

    def get_frame(self, t_rel: float) -> np.ndarray:
        """Get the image frame (same for all times)"""
        return self._image.copy()

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
