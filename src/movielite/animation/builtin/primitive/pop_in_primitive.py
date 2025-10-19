from typing import Tuple, Callable, Optional
from ...definitions import Transformer, OvershootConfig
from ...primitive_animation import PrimitiveAnimation
from pycaps.common import WordClip
from pycaps.layout import LayoutUtils

class PopInPrimitive(PrimitiveAnimation):
    def __init__(
        self,
        duration: float,
        delay: float = 0.0,
        transformer: Callable[[float], float] = Transformer.LINEAR,
        init_scale: float = 0.7,
        min_scale: float = 0.3,
        min_scale_at: float = 0.5,
        overshoot: Optional[OvershootConfig] = None,
    ) -> None:
        super().__init__(duration, delay, transformer)
        self._init_scale: float = init_scale
        self._min_scale: float = min_scale
        self._min_scale_at: float = min_scale_at
        self._overshoot: Optional[OvershootConfig] = overshoot

        if self._overshoot is not None and self._min_scale_at >= self._overshoot.peak_at:
            raise ValueError("min_scale_at must be less than overshoot.peak_at")

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        group_center = LayoutUtils.get_clip_container_center(clip, self._what)
        word_original_width = clip.layout.size.width
        word_original_height = clip.layout.size.height
        word_final_center_x = clip.layout.position.x + word_original_width / 2
        word_final_center_y = clip.layout.position.y + word_original_height / 2
    
        def get_size_factor(t: float) -> float:
            peak_at = self._overshoot.peak_at if self._overshoot is not None else 1.0
            overshoot_scale = 1 + self._overshoot.amount if self._overshoot is not None else 1.0

            if t < self._min_scale_at:
                progress = t / self._min_scale_at
                return self._init_scale + (self._min_scale - self._init_scale) * progress
            elif self._min_scale_at < t < peak_at:
                progress = (t - self._min_scale_at) / (peak_at - self._min_scale_at)
                return self._min_scale + (overshoot_scale - self._min_scale) * progress
            elif peak_at < t < 1.0:
                progress = (t - peak_at) / (1.0 - peak_at) if peak_at != 1.0 else 1.0
                return overshoot_scale + (1.0 - overshoot_scale) * progress
            else:
                return 1.0

        def get_position(t: float) -> Tuple[float, float]:
            scale = get_size_factor(t)
            current_width = word_original_width * scale
            current_height = word_original_height * scale

            current_center_x = group_center[0] + (word_final_center_x - group_center[0]) * t
            current_center_y = group_center[1] + (word_final_center_y - group_center[1]) * t

            final_x = current_center_x - (current_width / 2)
            final_y = current_center_y - (current_height / 2)
            
            return (final_x, final_y)

        self._apply_size(clip, offset, get_size_factor)
        self._apply_position(clip, offset, get_position)
