from typing import Tuple, Callable, Optional
from pycaps.common import WordClip, ElementType
from .definitions import Transformer
from abc import abstractmethod
from .animation import Animation

class PrimitiveAnimation(Animation):
    def __init__(
            self,
            duration: float,
            delay: float = 0.0,
            transformer: Callable[[float], float] = Transformer.LINEAR,
        ) -> None:
        super().__init__(duration, delay)
        self._transformer: Callable[[float], float] = transformer
        self._position_transform: Optional[Callable[[], None]] = None
        self._size_transform: Optional[Callable[[], None]] = None
        self._opacity_transform: Optional[Callable[[], None]] = None
        self._what: ElementType = ElementType.WORD

    @abstractmethod
    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        pass

    def run(self, clip: WordClip, offset: float, what: ElementType) -> None:
        self._what = what
        self._apply_animation(clip, offset)

        # apply transforms in order (order is important)
        if self._size_transform: self._size_transform()
        if self._position_transform: self._position_transform()
        if self._opacity_transform: self._opacity_transform()

    def _apply_position(self, clip: WordClip, offset: float, get_position_fn: Callable[[float], Tuple[float, float]]) -> None:
        old_position_transform = clip.media_clip.position
        def transform() -> None:
            def new_position_transform(t):
                if t + offset < 0 or t + offset > self._duration:
                    return old_position_transform(t)
                
                return get_position_fn(self._normalice_time(t + offset))

            clip.media_clip.set_position(new_position_transform)
        
        self._position_transform = transform

    def _apply_size(self, clip: WordClip, offset: float, get_resize_fn: Callable[[float], float]) -> None:
        old_scale_transform = clip.media_clip.scale
        def transform() -> None:
            def new_scale_tranform(t):
                if t + offset < 0: # or t + offset > self._duration:
                    return old_scale_transform(t)
                
                return get_resize_fn(self._normalice_time(t + offset))

            clip.media_clip.set_scale(new_scale_tranform)
        
        self._size_transform = transform
    
    def _apply_opacity(self, clip: WordClip, offset: float, get_opacity_fn: Callable[[float], float]) -> None:
        old_opacity_transform = clip.media_clip.opacity
        def transform() -> None:
            def new_opacity_transform(t):
                if t + offset < 0: #or t + offset > self._duration:
                    return old_opacity_transform(t)
                
                return get_opacity_fn(self._normalice_time(t + offset))

            clip.media_clip.set_opacity(new_opacity_transform)
        
        self._opacity_transform = transform

    def _normalice_time(self, t: float) -> float:
        '''
        Normalize the time to be between 0 and 1 using the duration of the animation
        And apply the easing function to the time
        '''
        if self._duration == 0:
            raise ValueError("Animation duration can't be 0")
        
        normalice = lambda n: min(1, max(0, n))
        progress = normalice(t / self._duration)
        return normalice(self._apply_transformer(progress))

    def _apply_transformer(self, t: float) -> float:
        if not isinstance(self._transformer, Callable):    
            raise ValueError(f"Invalid transformer: {self._transformer}")
        
        return self._transformer(t)
