from ...animation import Animation
from ...preset_animation import PresetAnimation
from ..primitive import PopInPrimitive, FadeInPrimitive
from typing import List
from ...definitions import OvershootConfig

class PopIn(PresetAnimation):

    def __init__(self, duration: float = 0.3, delay: float = 0.0):
        super().__init__(duration, delay)

    def _build_animations(self) -> List[Animation]:
        return [
            PopInPrimitive(
                duration=self._duration,
                delay=self._delay,
                overshoot=OvershootConfig(),
                min_scale=0.5,
                init_scale=0.5
            ),
            FadeInPrimitive(duration=self._duration, delay=self._delay)
        ]
