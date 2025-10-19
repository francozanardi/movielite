from ...animation import Animation
from ...preset_animation import PresetAnimation
from ..primitive import FadeInPrimitive
from typing import List

class FadeIn(PresetAnimation):

    def __init__(self, duration: float = 0.2, delay: float = 0.0):
        super().__init__(duration, delay)

    def _build_animations(self) -> List[Animation]:
        return [
            FadeInPrimitive(
                duration=self._duration,
                delay=self._delay,
            )
        ]
