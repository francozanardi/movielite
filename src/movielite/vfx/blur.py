import cv2
import numpy as np
from ..core import GraphicClip
from .base import GraphicEffect

class Blur(GraphicEffect):
    """
    Blur effect that applies Gaussian blur to the clip.
    Can be static (constant blur) or animated (blur changes over time).
    """

    def __init__(self, intensity: float = 5.0, animated: bool = False, duration: float = None):
        """
        Create a blur effect.

        Args:
            intensity: Blur intensity (kernel size). Higher = more blur. Must be odd number >= 1.
            animated: If True, blur increases from 0 to intensity over duration
            duration: Duration of the blur animation in seconds (only used if animated=True)
        """
        # Ensure kernel size is odd
        self.intensity = int(intensity)
        if self.intensity % 2 == 0:
            self.intensity += 1
        self.intensity = max(1, self.intensity)

        self.animated = animated
        self.duration = duration

        if animated and duration is None:
            raise ValueError("duration must be specified when animated=True")

    def apply(self, clip: GraphicClip) -> None:
        """Apply blur effect by adding a frame transform"""

        if not self.animated:
            # Static blur
            def blur_transform(frame: np.ndarray, t: float) -> np.ndarray:
                if self.intensity <= 1:
                    return frame
                return cv2.GaussianBlur(frame, (self.intensity, self.intensity), 0)

            clip.add_transform(blur_transform)
        else:
            # Animated blur (increases over time)
            def blur_transform(frame: np.ndarray, t: float) -> np.ndarray:
                if t >= self.duration:
                    kernel_size = self.intensity
                else:
                    # Linear interpolation from 1 to intensity
                    progress = t / self.duration
                    kernel_size = int(1 + (self.intensity - 1) * progress)
                    # Ensure odd
                    if kernel_size % 2 == 0:
                        kernel_size += 1

                if kernel_size <= 1:
                    return frame

                return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

            clip.add_transform(blur_transform)


class BlurIn(GraphicEffect):
    """
    Blur-in effect that starts blurred and gradually becomes sharp.
    """

    def __init__(self, duration: float, max_intensity: float = 15.0):
        """
        Create a blur-in effect.

        Args:
            duration: Duration of the blur-in effect in seconds
            max_intensity: Maximum blur intensity at the start
        """
        self.duration = duration
        self.max_intensity = int(max_intensity)
        if self.max_intensity % 2 == 0:
            self.max_intensity += 1

    def apply(self, clip: GraphicClip) -> None:
        """Apply blur-in effect by adding a frame transform"""

        def blur_in_transform(frame: np.ndarray, t: float) -> np.ndarray:
            if t >= self.duration:
                return frame

            # Blur decreases over time
            progress = t / self.duration
            kernel_size = int(self.max_intensity * (1.0 - progress))

            # Ensure odd and at least 1
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel_size = max(1, kernel_size)

            if kernel_size <= 1:
                return frame

            return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

        clip.add_transform(blur_in_transform)


class BlurOut(GraphicEffect):
    """
    Blur-out effect that starts sharp and gradually becomes blurred.
    """

    def __init__(self, duration: float, max_intensity: float = 15.0):
        """
        Create a blur-out effect.

        Args:
            duration: Duration of the blur-out effect in seconds
            max_intensity: Maximum blur intensity at the end
        """
        self.duration = duration
        self.max_intensity = int(max_intensity)
        if self.max_intensity % 2 == 0:
            self.max_intensity += 1

    def apply(self, clip: GraphicClip) -> None:
        """Apply blur-out effect by adding a frame transform"""
        clip_duration = clip.duration

        def blur_out_transform(frame: np.ndarray, t: float) -> np.ndarray:
            # Apply blur at the end of the clip
            if t < clip_duration - self.duration:
                return frame

            # Blur increases over time
            time_in_effect = t - (clip_duration - self.duration)
            progress = time_in_effect / self.duration
            kernel_size = int(1 + (self.max_intensity - 1) * progress)

            # Ensure odd
            if kernel_size % 2 == 0:
                kernel_size += 1

            if kernel_size <= 1:
                return frame

            return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

        clip.add_transform(blur_out_transform)
