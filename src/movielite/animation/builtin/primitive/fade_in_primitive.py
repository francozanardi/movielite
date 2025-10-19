from ...primitive_animation import PrimitiveAnimation
from pycaps.common import WordClip

class FadeInPrimitive(PrimitiveAnimation):
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        self._apply_opacity(clip, offset, lambda t: t)
