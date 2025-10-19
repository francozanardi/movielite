from ...animation import Animation
from ...preset_animation import PresetAnimation
from ..primitive import ZoomInPrimitive, FadeInPrimitive
from typing import List
from ...definitions import OvershootConfig, Transformer

class ZoomIn(PresetAnimation):

    def __init__(self, duration: float = 0.3, delay: float = 0.0):
        super().__init__(duration, delay)

    def _build_animations(self) -> List[Animation]:
        return [
            ZoomInPrimitive(
                duration=self._duration,
                delay=self._delay,
                overshoot=OvershootConfig(),
                transformer=Transformer.EASE_OUT
            ),
            FadeInPrimitive(
                duration=self._duration*0.5,
                delay=self._delay,
            )
        ]
