from ...animation import Animation
from ...preset_animation import PresetAnimation
from ..primitive import ZoomInPrimitive, FadeInPrimitive
from typing import List
from ...definitions import Transformer

class ZoomOut(PresetAnimation):

    def __init__(self, duration: float = 0.3, delay: float = 0.0):
        super().__init__(duration, delay)

    def _build_animations(self) -> List[Animation]:
        return [
            ZoomInPrimitive(
                duration=self._duration,
                delay=self._delay,
                init_scale=0.2,
                transformer=Transformer.INVERT
            ),
            FadeInPrimitive(
                duration=self._duration,
                delay=self._delay,
                transformer=Transformer.INVERT
            )
        ]
