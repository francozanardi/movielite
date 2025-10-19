from ...animation import Animation
from ...preset_animation import PresetAnimation
from typing import List
from ...definitions import Transformer
from ..primitive import FadeInPrimitive

class FadeOut(PresetAnimation):

    def __init__(self, duration: float = 0.2, delay: float = 0.0):
        super().__init__(duration, delay)

    def _build_animations(self) -> List[Animation]:
        return [
            FadeInPrimitive(
                duration=self._duration,
                delay=self._delay,
                transformer=Transformer.INVERT
            )
        ]
