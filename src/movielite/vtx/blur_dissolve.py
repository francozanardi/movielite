import cv2
import numpy as np
from ..core import GraphicClip
from ..video import VideoClip
from .base import Transition

class BlurDissolve(Transition):
    """
    Blur dissolve transition where the first clip blurs and fades out,
    while the second clip fades in sharply.

    This transition does NOT require overlapping clips - they can be consecutive.
    """

    def __init__(self, duration: float, max_blur: int = 21):
        """
        Create a blur dissolve transition.

        Args:
            duration: Duration of the transition effect in seconds
            max_blur: Maximum blur intensity (kernel size). Must be odd. Default: 21
        """
        self.duration = duration
        self.max_blur = int(max_blur)
        # Ensure kernel size is odd
        if self.max_blur % 2 == 0:
            self.max_blur += 1
        self.max_blur = max(3, self.max_blur)

    def apply(self, clip1: GraphicClip, clip2: GraphicClip) -> None:
        """
        Apply blur dissolve transition between two clips.

        Args:
            clip1: Outgoing clip (blurs and fades out at the end)
            clip2: Incoming clip (fades in sharply at the beginning)
        """
        # Validate clips are consecutive (allows gaps)
        self._validate_clips_are_consecutive(clip1, clip2, allow_gap=True)

        # Apply blur + fade out to clip1
        original_opacity_1 = clip1.opacity
        clip1_duration = clip1.duration

        def clip1_blur_fadeout_transform(frame: np.ndarray, t: float) -> np.ndarray:
            # Only apply at the end of clip1
            if t <= clip1_duration - self.duration:
                return frame

            # Calculate progress (0 to 1)
            fade_progress = (t - (clip1_duration - self.duration)) / self.duration

            # Apply increasing blur
            kernel_size = int(1 + (self.max_blur - 1) * fade_progress)
            # Ensure odd
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel_size = max(1, min(kernel_size, self.max_blur))

            if kernel_size > 1:
                frame = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)

            return frame

        def clip1_opacity_with_fadeout(t):
            if t > clip1_duration - self.duration:
                fade_progress = (t - (clip1_duration - self.duration)) / self.duration
                return original_opacity_1(t) * (1.0 - fade_progress)
            return original_opacity_1(t)

        clip1.add_transform(clip1_blur_fadeout_transform)
        clip1.set_opacity(clip1_opacity_with_fadeout)

        # Apply fade in to clip2 (sharp, no blur)
        original_opacity_2 = clip2.opacity

        def clip2_opacity_with_fadein(t):
            if t < self.duration:
                fade_progress = t / self.duration
                return original_opacity_2(t) * fade_progress
            return original_opacity_2(t)

        clip2.set_opacity(clip2_opacity_with_fadein)
