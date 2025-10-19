from pycaps.common import WordClip
from pycaps.layout import LayoutUtils
from typing import Tuple, Callable, Optional
from ...definitions import Transformer, OvershootConfig
from ...primitive_animation import PrimitiveAnimation

# TODO: it has an error while size is being animated, it's probably a precision error (because of using floats for the size in the scale)
# To notice it, you need to use a color background for a whole line, and run this animation over the line.
class ZoomInPrimitive(PrimitiveAnimation):

    def __init__(
        self,
        duration: float,
        delay: float = 0.0,
        transformer: Callable[[float], float] = Transformer.LINEAR,
        init_scale: float = 0.5,
        overshoot: Optional[OvershootConfig] = None,
    ) -> None:
        super().__init__(duration, delay, transformer)
        self._init_scale: float = init_scale
        self._overshoot: Optional[OvershootConfig] = overshoot

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        group_center = LayoutUtils.get_clip_container_center(clip, self._what)
        word_final_center = (
            clip.layout.position.x + clip.layout.size.width / 2,
            clip.layout.position.y + clip.layout.size.height / 2
        )
        relative_pos_vector = (
            word_final_center[0] - group_center[0],
            word_final_center[1] - group_center[1]
        )

        def get_size_factor(t: float) -> float:
            if self._overshoot is None:
                return self._init_scale + (1.0 - self._init_scale) * t
            
            if t < self._overshoot.peak_at:
                progress = t / self._overshoot.peak_at
                start_offset = self._init_scale
                target_offset = 1 + self._overshoot.amount
                return start_offset + (target_offset - start_offset) * progress
            
            progress = (t - self._overshoot.peak_at) / (1.0 - self._overshoot.peak_at)
            start_offset = 1 + self._overshoot.amount
            target_offset = 1
            return start_offset - (start_offset - target_offset) * progress

        def get_position(t: float) -> Tuple[float, float]:
            progress = get_size_factor(t)
            
            current_width = clip.layout.size.width * progress
            current_height = clip.layout.size.height * progress

            current_center_x = group_center[0] + (relative_pos_vector[0] * progress)
            current_center_y = group_center[1] + (relative_pos_vector[1] * progress)

            final_x = current_center_x - (current_width / 2)
            final_y = current_center_y - (current_height / 2)
            
            return (final_x, final_y)

        self._apply_position(clip, offset, get_position)
        self._apply_size(clip, offset, get_size_factor)