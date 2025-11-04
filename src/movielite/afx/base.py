from abc import ABC, abstractmethod
from ..audio import AudioClip

class AudioEffect(ABC):
    """Base class for audio effects that can be applied to AudioClip instances"""

    @abstractmethod
    def apply(self, clip: 'AudioClip') -> None:
        """
        Apply this effect to a clip by modifying its properties.

        Args:
            clip: The AudioClip to apply the effect to
        """
        pass
