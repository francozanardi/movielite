from pycaps.common import WordClip, ElementType
from abc import ABC, abstractmethod

class Animation(ABC):
    def __init__(self, duration: float, delay: float = 0.0) -> None:
        self._duration: float = duration
        self._delay: float = delay

    @abstractmethod
    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        pass
