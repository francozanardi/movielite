from ..core import GraphicClip
from ..video import VideoClip
from .base import Transition
import numpy as np

class CrossFade(Transition):
    """
    CrossFade transition that smoothly blends from one clip to another.

    The first clip fades out while the second clip fades in over the specified duration.
    This applies to both video and audio (if the clips are VideoClips with audio).
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

        # Apply video crossfade
        original_opacity_1 = clip1.opacity
        original_opacity_2 = clip2.opacity
        clip1_duration = clip1.duration

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

        # Apply audio crossfade if clips are VideoClips with audio
        if isinstance(clip1, VideoClip) and isinstance(clip2, VideoClip):
            if clip1.audio.has_audio and clip2.audio.has_audio:
                self._apply_audio_crossfade(clip1, clip2)

    def _apply_audio_crossfade(self, clip1: VideoClip, clip2: VideoClip) -> None:
        """Apply crossfade to the audio tracks of two video clips"""
        audio1 = clip1.audio
        audio2 = clip2.audio

        clip1_duration = clip1.duration
        fade_start_time = audio1.offset + clip1_duration - self.duration

        # Fade out audio1 at the end
        def audio1_fadeout(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
            if t + len(samples) / sr < fade_start_time:
                return samples

            n_samples = len(samples)
            result = samples.copy()

            for i in range(n_samples):
                sample_time = t + i / sr
                if sample_time >= fade_start_time:
                    fade_progress = (sample_time - fade_start_time) / self.duration
                    fade_factor = max(0, min(1, 1.0 - fade_progress))
                    result[i] *= fade_factor

            return result

        # Fade in audio2 at the beginning
        fade_end_time = audio2.offset + self.duration

        def audio2_fadein(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
            if t >= fade_end_time:
                return samples

            n_samples = len(samples)
            result = samples.copy()

            for i in range(n_samples):
                sample_time = t + i / sr
                if sample_time < fade_end_time:
                    fade_progress = (sample_time - audio2._offset) / self.duration
                    fade_factor = max(0, min(1, fade_progress))
                    result[i] *= fade_factor

            return result

        audio1.add_transform(audio1_fadeout)
        audio2.add_transform(audio2_fadein)
