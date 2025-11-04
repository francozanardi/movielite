from .base import GraphicEffect
from ..core import GraphicClip

class FadeIn(GraphicEffect):
    """
    Fade in effect for graphic clips.
    Gradually increases opacity from 0 to the clip's original opacity over the specified duration.
    """

    def __init__(self, duration: float):
        """
        Create a fade in effect.

        Args:
            duration: Duration of the fade in seconds (from the start of the clip)
        """
        self.duration = duration

    def apply(self, clip: 'GraphicClip') -> None:
        """Apply fade in effect by modifying the clip's opacity function"""
        original_opacity = clip.opacity

        def opacity_with_fade_in(t):
            if t < self.duration:
                fade_progress = t / self.duration
                return original_opacity(t) * fade_progress
            return original_opacity(t)

        clip.set_opacity(opacity_with_fade_in)


class FadeOut(GraphicEffect):
    """
    Fade out effect for graphic clips.
    Gradually decreases opacity from the clip's original opacity to 0 over the specified duration.
    """

    def __init__(self, duration: float):
        """
        Create a fade out effect.

        Args:
            duration: Duration of the fade in seconds (at the end of the clip)
        """
        self.duration = duration

    def apply(self, clip: 'GraphicClip') -> None:
        """Apply fade out effect by modifying the clip's opacity function"""
        original_opacity = clip.opacity
        clip_duration = clip.duration

        def opacity_with_fade_out(t):
            if t > clip_duration - self.duration:
                fade_progress = (t - (clip_duration - self.duration)) / self.duration
                return original_opacity(t) * (1.0 - fade_progress)
            return original_opacity(t)

        clip.set_opacity(opacity_with_fade_out)
