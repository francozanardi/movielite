import numpy as np
from typing import Optional
from ..core import GraphicClip
from ..logger import get_logger
import cv2
from pictex import Canvas

class TextClip(GraphicClip):
    """
    A text clip that renders text using the pictex library.
    """

    def __init__(self, text: str, start: float = 0, duration: float = 5.0, canvas: Optional[Canvas] = None):
        """
        Create a text clip.

        Args:
            text: The text to render
            start: Start time in the composition (seconds)
            duration: How long to display the text (seconds)
            canvas: A pictex Canvas instance with styling configured.
                   If None, uses default styling.

        Example:
            >>> from pictex import Canvas, LinearGradient, Shadow
            >>> canvas = (
            ...     Canvas()
            ...     .font_family("Arial")
            ...     .font_size(60)
            ...     .color("white")
            ...     .padding(20)
            ...     .background_color(LinearGradient(["#2C3E50", "#FD746C"]))
            ...     .border_radius(10)
            ... )
            >>> clip = TextClip("Hello World!", duration=3, canvas=canvas)
        """
        if Canvas is None:
            raise ImportError("pictex is required for TextClip. Install it with: pip install pictex")

        super().__init__(start, duration)

        self._text = text
        self._canvas = canvas if canvas is not None else self._get_default_canvas()

        # Render the text to get the image
        rendered = self._canvas.render(text)
        img_bgra = rendered.to_numpy(mode='BGRA')
        self._image = img_bgra.astype(np.uint8)
        self._size = (self._image.shape[1], self._image.shape[0])
        self._original_image = self._image  # Keep original for potential re-resizing

        get_logger().debug(f"TextClip created: text='{text}', size={self._size}, shape={self._image.shape}")

    def get_frame(self, t_rel: float) -> np.ndarray:
        """Get the rendered text frame (same for all times)"""
        return self._image

    def _apply_resize(self, frame: np.ndarray) -> np.ndarray:
        interpolation = cv2.INTER_AREA if (self._target_size[0] < self._size[0]) else cv2.INTER_CUBIC
        self._image = cv2.resize(self._original_image, self._target_size, interpolation=interpolation)
        self._size = self._target_size
        self._target_size = None
        return self._image

    def _convert_to_mask(self, frame: np.ndarray) -> np.ndarray:
        """Convert text frame to 2D mask (0-255 uint8)"""
        if frame.shape[2] == 4:
            # Use alpha channel
            mask = frame[:, :, 3]
        else:
            # Convert to grayscale
            mask = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return mask

    def _get_default_canvas(self) -> 'Canvas':
        """Get a default canvas with basic styling"""
        return (
            Canvas()
            .font_size(48)
            .color("white")
            .background_color("transparent")
            .padding(10)
        )

    @property
    def text(self):
        """Get the text content"""
        return self._text
