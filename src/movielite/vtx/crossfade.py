from ..core import GraphicClip
from .base import Transition

class CrossFade(Transition):
    """
    CrossFade transition that smoothly blends from one clip to another.

    The first clip fades out while the second clip fades in over the specified duration.
    This requires the clips to have overlapping time ranges.
    """

    def __init__(self, duration: float):
        """
        Create a crossfade transition.

        Args:
            duration: Duration of the crossfade in seconds
        """
        self.duration = duration

    def apply(self, clip1: GraphicClip, clip2: GraphicClip) -> None:
        """
        Apply crossfade transition between two clips.

        Args:
            clip1: Outgoing clip (fades out at the end)
            clip2: Incoming clip (fades in at the beginning)

        Raises:
            ValueError: If clips don't overlap properly for the transition
        """
        self._validate_clips_have_overlap(clip1, clip2, self.duration)

        original_opacity_1 = clip1._opacity
        original_opacity_2 = clip2._opacity
        clip1_duration = clip1._duration

        def clip1_opacity_with_fadeout(t):
            if t > clip1_duration - self.duration:
                fade_progress = (t - (clip1_duration - self.duration)) / self.duration
                return original_opacity_1(t) * (1.0 - fade_progress)
            return original_opacity_1(t)

        def clip2_opacity_with_fadein(t):
            if t < self.duration:
                fade_progress = t / self.duration
                return original_opacity_2(t) * fade_progress
            return original_opacity_2(t)

        clip1.set_opacity(clip1_opacity_with_fadeout)
        clip2.set_opacity(clip2_opacity_with_fadein)
