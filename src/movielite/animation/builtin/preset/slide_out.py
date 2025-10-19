from ...animation import Animation
from ...preset_animation import PresetAnimation
from ..primitive import SlideInPrimitive, FadeInPrimitive
from typing import List
from ...definitions import Transformer, Direction

class SlideOut(PresetAnimation):

    def __init__(self, direction: Direction = Direction.RIGHT, duration: float = 0.3, delay: float = 0.0) -> None:
        super().__init__(duration, delay)
        self._direction: Direction = direction

    def _build_animations(self) -> List[Animation]:
        return [
            SlideInPrimitive(
                duration=self._duration,
                delay=self._delay,
                direction=self._direction,
                transformer=Transformer.INVERT
            ),
            FadeInPrimitive(
                duration=self._duration,
                delay=self._delay,
                transformer=Transformer.INVERT
            )
        ]
