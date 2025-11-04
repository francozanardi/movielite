import numpy as np
from .base import AudioEffect
from ..audio import AudioClip

class FadeIn(AudioEffect):
    """
    Fade in effect for audio clips.
    Gradually increases volume from 0 to the clip's original volume over the specified duration.
    """

    def __init__(self, duration: float):
        """
        Create a fade in effect.

        Args:
            duration: Duration of the fade in seconds (from the start of the clip)
        """
        self.duration = duration

    def apply(self, clip: 'AudioClip') -> None:
        """Apply fade in effect by adding a transform to the clip"""
        fade_start = clip._offset
        fade_end = clip._offset + self.duration

        def fade_in_transform(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
            if t >= fade_end:
                return samples

            n_samples = len(samples)
            result = samples.copy()

            for i in range(n_samples):
                sample_time = t + i / sr
                if sample_time < fade_end:
                    fade_factor = (sample_time - fade_start) / self.duration
                    result[i] *= max(0, min(1, fade_factor))

            return result

        clip._sample_transforms.append(fade_in_transform)


class FadeOut(AudioEffect):
    """
    Fade out effect for audio clips.
    Gradually decreases volume from the clip's original volume to 0 over the specified duration.
    """

    def __init__(self, duration: float):
        """
        Create a fade out effect.

        Args:
            duration: Duration of the fade in seconds (at the end of the clip)
        """
        self.duration = duration

    def apply(self, clip: 'AudioClip') -> None:
        """Apply fade out effect by adding a transform to the clip"""
        fade_start = clip._offset + clip._duration - self.duration
        fade_end = clip._offset + clip._duration

        def fade_out_transform(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
            if t + len(samples) / sr < fade_start:
                return samples

            n_samples = len(samples)
            result = samples.copy()

            for i in range(n_samples):
                sample_time = t + i / sr
                if sample_time >= fade_start:
                    fade_factor = (fade_end - sample_time) / self.duration
                    result[i] *= max(0, min(1, fade_factor))

            return result

        clip._sample_transforms.append(fade_out_transform)
