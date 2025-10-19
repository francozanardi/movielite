from pycaps.common import ElementType, WordClip
from typing import List
from .animation import Animation
from abc import abstractmethod

class PresetAnimation(Animation):
    def __init__(self, duration: float, delay: float = 0.0) -> None:
        super().__init__(duration, delay)

    @abstractmethod
    def _build_animations(self) -> List[Animation]:
        pass

    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        for animation in self._build_animations():
            animation.run(clip, offset, what)
