from abc import ABC, abstractmethod
from ..core import GraphicClip

class GraphicEffect(ABC):
    """Base class for visual effects that can be applied to GraphicClip instances"""

    @abstractmethod
    def apply(self, clip: 'GraphicClip') -> None:
        """
        Apply this effect to a clip by modifying its properties.

        Args:
            clip: The GraphicClip to apply the effect to
        """
        pass
