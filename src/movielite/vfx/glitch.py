import cv2
import numpy as np
from ..core import GraphicClip
from .base import GraphicEffect

class Glitch(GraphicEffect):
    """
    Glitch effect that creates digital distortion artifacts.
    Simulates VHS glitches, digital corruption, and RGB channel shifts.
    """

    def __init__(
        self,
        intensity: float = 0.5,
        rgb_shift: bool = True,
        horizontal_lines: bool = True,
        scan_lines: bool = False
    ):
        """
        Create a glitch effect.

        Args:
            intensity: Intensity of the glitch effect (0.0 to 1.0)
            rgb_shift: Enable RGB channel shifting
            horizontal_lines: Enable horizontal displacement lines
            scan_lines: Enable scan line artifacts
        """
        self.intensity = max(0.0, min(1.0, intensity))
        self.rgb_shift = rgb_shift
        self.horizontal_lines = horizontal_lines
        self.scan_lines = scan_lines

    def apply(self, clip: GraphicClip) -> None:
        """Apply glitch effect by adding a frame transform"""

        def glitch_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.intensity == 0.0:
                return frame

            result = frame.copy()
            h, w = frame.shape[:2]

            # Use time as seed for pseudo-random but consistent glitches
            seed = int(t * 1000) % 1000
            np.random.seed(seed)

            # RGB Channel Shift
            if self.rgb_shift:
                shift_amount = int(w * 0.02 * self.intensity)
                if shift_amount > 0:
                    # Shift red channel
                    result[:, shift_amount:, 2] = frame[:, :-shift_amount, 2]
                    # Shift blue channel (opposite direction)
                    result[:, :-shift_amount, 0] = frame[:, shift_amount:, 0]

            # Horizontal displacement lines
            if self.horizontal_lines:
                num_glitch_lines = int(5 * self.intensity)
                for _ in range(num_glitch_lines):
                    y_pos = np.random.randint(0, h - 1)
                    line_height = np.random.randint(1, int(h * 0.05 * self.intensity) + 1)
                    shift_amount = np.random.randint(-int(w * 0.1 * self.intensity),
                                                     int(w * 0.1 * self.intensity))

                    if shift_amount != 0:
                        y_end = min(y_pos + line_height, h)
                        if shift_amount > 0:
                            result[y_pos:y_end, shift_amount:] = frame[y_pos:y_end, :-shift_amount]
                        else:
                            result[y_pos:y_end, :shift_amount] = frame[y_pos:y_end, -shift_amount:]

            # Scan lines
            if self.scan_lines:
                scan_line_mask = np.ones((h, w), dtype=np.float32)
                scan_line_mask[::2] = 1.0 - (0.15 * self.intensity)
                scan_line_mask = np.stack([scan_line_mask] * 3, axis=2)
                result = (result.astype(np.float32) * scan_line_mask).astype(np.uint8)

            return result

        clip.add_transform(glitch_transform)


class ChromaticAberration(GraphicEffect):
    """
    Chromatic aberration effect that separates RGB channels.
    Creates a lens distortion look.
    """

    def __init__(self, intensity: float = 5.0):
        """
        Create a chromatic aberration effect.

        Args:
            intensity: Intensity of the aberration in pixels
        """
        self.intensity = int(max(0, intensity))

    def apply(self, clip: GraphicClip) -> None:
        """Apply chromatic aberration by adding a frame transform"""

        def chromatic_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.intensity == 0:
                return frame

            h, w = frame.shape[:2]
            result = frame.copy()

            # Shift red channel right
            if self.intensity < w:
                result[:, self.intensity:, 2] = frame[:, :-self.intensity, 2]

            # Shift blue channel left
            if self.intensity < w:
                result[:, :-self.intensity, 0] = frame[:, self.intensity:, 0]

            return result

        clip.add_transform(chromatic_transform)


class Pixelate(GraphicEffect):
    """
    Pixelate effect that reduces resolution to create a blocky appearance.
    """

    def __init__(self, block_size: int = 10):
        """
        Create a pixelate effect.

        Args:
            block_size: Size of pixelation blocks in pixels
        """
        self.block_size = max(1, int(block_size))

    def apply(self, clip: GraphicClip) -> None:
        """Apply pixelate effect by adding a frame transform"""

        def pixelate_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.block_size <= 1:
                return frame

            h, w = frame.shape[:2]

            # Downscale
            small_h = max(1, h // self.block_size)
            small_w = max(1, w // self.block_size)
            small = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_LINEAR)

            # Upscale back with nearest neighbor for blocky effect
            pixelated = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)

            return pixelated

        clip.add_transform(pixelate_transform)
