import cv2
import numpy as np
from ..core import GraphicClip
from .base import GraphicEffect

class Saturation(GraphicEffect):
    """
    Adjust saturation of the clip.
    """

    def __init__(self, factor: float = 1.0):
        """
        Create a saturation effect.

        Args:
            factor: Saturation multiplier.
                    1.0 = no change
                    0.0 = grayscale
                    >1.0 = more saturated
                    <1.0 = less saturated
        """
        self.factor = max(0.0, factor)

    def apply(self, clip: GraphicClip) -> None:
        """Apply saturation adjustment by adding a frame transform"""

        def saturation_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.factor == 1.0:
                return frame

            # Convert BGR to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)

            # Adjust saturation channel
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.factor, 0, 255)

            # Convert back to BGR
            hsv = hsv.astype(np.uint8)
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        clip.add_transform(saturation_transform)


class Brightness(GraphicEffect):
    """
    Adjust brightness of the clip.
    """

    def __init__(self, factor: float = 1.0):
        """
        Create a brightness effect.

        Args:
            factor: Brightness multiplier.
                    1.0 = no change
                    >1.0 = brighter
                    <1.0 = darker
        """
        self.factor = max(0.0, factor)

    def apply(self, clip: GraphicClip) -> None:
        """Apply brightness adjustment by adding a frame transform"""

        def brightness_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.factor == 1.0:
                return frame

            # Convert to float, apply brightness, clip, convert back
            adjusted = frame.astype(np.float32) * self.factor
            return np.clip(adjusted, 0, 255).astype(np.uint8)

        clip.add_transform(brightness_transform)


class Contrast(GraphicEffect):
    """
    Adjust contrast of the clip.
    """

    def __init__(self, factor: float = 1.0):
        """
        Create a contrast effect.

        Args:
            factor: Contrast multiplier.
                    1.0 = no change
                    >1.0 = more contrast
                    <1.0 = less contrast
        """
        self.factor = factor

    def apply(self, clip: GraphicClip) -> None:
        """Apply contrast adjustment by adding a frame transform"""

        def contrast_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.factor == 1.0:
                return frame

            # Convert to float
            frame_float = frame.astype(np.float32)

            # Apply contrast formula: output = (input - 128) * factor + 128
            adjusted = (frame_float - 128) * self.factor + 128

            # Clip and convert back
            return np.clip(adjusted, 0, 255).astype(np.uint8)

        clip.add_transform(contrast_transform)


class BlackAndWhite(GraphicEffect):
    """
    Convert clip to black and white (grayscale).
    """

    def __init__(self):
        """Create a black and white effect."""
        pass

    def apply(self, clip: GraphicClip) -> None:
        """Apply black and white effect by adding a frame transform"""

        def bw_transform(frame: np.ndarray, t: float) -> np.ndarray:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Convert back to BGR (but as grayscale)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        clip.add_transform(bw_transform)


class Grayscale(BlackAndWhite):
    """Alias for BlackAndWhite effect."""
    pass


class Sepia(GraphicEffect):
    """
    Apply sepia tone effect to the clip.
    """

    def __init__(self, intensity: float = 1.0):
        """
        Create a sepia effect.

        Args:
            intensity: Intensity of the sepia effect (0.0 to 1.0)
                      1.0 = full sepia
                      0.0 = no effect
        """
        self.intensity = max(0.0, min(1.0, intensity))

    def apply(self, clip: GraphicClip) -> None:
        """Apply sepia effect by adding a frame transform"""

        def sepia_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.intensity == 0.0:
                return frame

            # Sepia transformation matrix (BGR order)
            sepia_kernel = np.array([
                [0.131, 0.534, 0.272],  # B
                [0.168, 0.686, 0.349],  # G
                [0.189, 0.769, 0.393]   # R
            ])

            # Apply transformation
            sepia_frame = cv2.transform(frame, sepia_kernel)

            # Blend with original based on intensity
            if self.intensity < 1.0:
                sepia_frame = cv2.addWeighted(
                    frame, 1.0 - self.intensity,
                    sepia_frame, self.intensity,
                    0
                )

            return np.clip(sepia_frame, 0, 255).astype(np.uint8)

        clip.add_transform(sepia_transform)
