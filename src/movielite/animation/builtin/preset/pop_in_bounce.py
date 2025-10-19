from ...animation import Animation
from ...preset_animation import PresetAnimation
from ..primitive import PopInPrimitive, FadeInPrimitive
from typing import List
from ...definitions import OvershootConfig

class PopInBounce(PresetAnimation):

    def __init__(self, duration: float = 0.4, delay: float = 0.0):
        super().__init__(duration, delay)

    def _build_animations(self) -> List[Animation]:
        return [
            PopInPrimitive(
                duration=self._duration,
                delay=self._delay,
                overshoot=OvershootConfig()
            ),
            FadeInPrimitive(duration=self._duration*0.2, delay=self._delay)
        ]
