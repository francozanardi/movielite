from ...primitive_animation import PrimitiveAnimation
from ...definitions import Direction, OvershootConfig, Transformer
from pycaps.common import WordClip
from typing import Tuple, Callable, Optional

class SlideInPrimitive(PrimitiveAnimation):
    def __init__(
            self,
            duration: float,
            delay: float = 0.0,
            transformer: Callable[[float], float] = Transformer.LINEAR,
            direction: Direction = Direction.LEFT,
            distance: float = 100,
            overshoot: Optional[OvershootConfig] = None,
        ) -> None:
        super().__init__(duration, delay, transformer)
        self._direction: Direction = direction
        self._distance: float = distance
        self._overshoot: Optional[OvershootConfig] = overshoot

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        final_pos = clip.layout.position

        def get_displacement(t: float) -> float:
            if self._overshoot is None:
                return self._distance * (t-1)
            
            overshoot_distance = self._distance * self._overshoot.amount
            if t < self._overshoot.peak_at:
                progress = t / self._overshoot.peak_at
                start_offset = -(self._distance)
                target_offset = overshoot_distance
                return start_offset + (target_offset - start_offset) * progress
            else:
                progress = (t - self._overshoot.peak_at) / (1.0 - self._overshoot.peak_at)
                start_offset = overshoot_distance
                target_offset = 0
                return start_offset + (target_offset - start_offset) * progress
                
        def get_position(t: float) -> Tuple[float, float]:
            current_displacement = get_displacement(t)

            if self._direction == Direction.LEFT:
                return final_pos.x + current_displacement, final_pos.y
            elif self._direction == Direction.RIGHT:
                return final_pos.x - current_displacement, final_pos.y
            elif self._direction == Direction.UP:
                return final_pos.x, final_pos.y + current_displacement
            elif self._direction == Direction.DOWN:
                return final_pos.x, final_pos.y - current_displacement
            return final_pos.x, final_pos.y


        self._apply_position(clip, offset, get_position)
