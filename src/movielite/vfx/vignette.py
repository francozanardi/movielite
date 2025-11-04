import cv2
import numpy as np
from ..core import GraphicClip
from .base import GraphicEffect

class Vignette(GraphicEffect):
    """
    Apply vignette effect that darkens the edges of the frame.
    """

    def __init__(self, intensity: float = 0.5, radius: float = 0.8):
        """
        Create a vignette effect.

        Args:
            intensity: Darkness intensity at the edges (0.0 to 1.0)
                      0.0 = no effect
                      1.0 = black edges
            radius: Radius of the bright center area (0.0 to 1.0)
                   0.0 = small bright area
                   1.0 = large bright area (almost no vignette)
        """
        self.intensity = max(0.0, min(1.0, intensity))
        self.radius = max(0.0, min(1.0, radius))

    def apply(self, clip: GraphicClip) -> None:
        """Apply vignette effect by adding a frame transform"""

        # Cache for the vignette mask (created once per frame size)
        vignette_cache = {}

        def vignette_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if self.intensity == 0.0:
                return frame

            h, w = frame.shape[:2]
            cache_key = (w, h)

            # Create vignette mask if not cached
            if cache_key not in vignette_cache:
                # Create radial gradient
                center_x, center_y = w // 2, h // 2

                # Create coordinate grids
                Y, X = np.ogrid[:h, :w]

                # Calculate distance from center (normalized)
                dist_from_center = np.sqrt(((X - center_x) / w) ** 2 + ((Y - center_y) / h) ** 2)

                # Create vignette mask
                # Areas within radius = 1.0 (full brightness)
                # Areas beyond radius fade to (1 - intensity)
                mask = np.clip(1.0 - (dist_from_center / self.radius), 0, 1)
                mask = 1.0 - (1.0 - mask) * self.intensity

                # Expand to 3 channels if needed
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    mask = np.stack([mask, mask, mask], axis=2)

                vignette_cache[cache_key] = mask

            # Apply vignette
            mask = vignette_cache[cache_key]
            vignetted = (frame.astype(np.float32) * mask).astype(np.uint8)

            return vignetted

        clip.add_transform(vignette_transform)
