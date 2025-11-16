from typing import List, Optional
from movielite import GraphicClip
import numpy as np
import cv2
from ..core import empty_frame

try:
    from typing import Self # type: ignore[attr-defined]
except ImportError:
    from typing_extensions import Self

class CompositeClip(GraphicClip):
    """
    A composite clip that combines multiple graphic clips into a single unit.

    PERFORMANCE NOTE: CompositeClip should only be used when you need to treat multiple
    clips as a single unit (e.g., to apply transforms, effects, or positioning to the
    entire group). For most use cases, directly adding clips to VideoWriter using
    add_clips() is more performant, as it avoids the overhead of creating an
    intermediate composition layer.

    Use CompositeClip when:
    - You need to apply transformations (position, scale, opacity) to a group of clips
    - You need to treat multiple clips as a single reusable component
    - You need to mask or apply effects to a composition of clips

    Use VideoWriter.add_clips() when:
    - You're just compositing clips at fixed positions
    - You don't need to treat the clips as a single unit

    All clip timings (start, duration) and positions within a CompositeClip are relative
    to the composite's own start time and position. For example, if a CompositeClip starts
    at t=5s and contains a clip with start=2s, that inner clip will appear at t=7s in the
    final composition.

    You must explicitly specify the start time of the CompositeClip.
    The start/duration of child clips are interpreted relative to the composite, not absolute.
    Duration can be auto-calculated from child clips or specified explicitly.

    Example:
        >>> from movielite import ImageClip, TextClip, VideoWriter, CompositeClip
        >>>
        >>> # Create clips with RELATIVE timings (relative to composite)
        >>> background = ImageClip("background.png", start=0, duration=5)
        >>> text = TextClip("Hello", start=1, duration=3)  # Appears 1s after composite starts
        >>> text.set_position((50, 50))
        >>>
        >>> # Create composite with explicit start, auto-calculated duration
        >>> composite = CompositeClip(
        >>>     clips=[background, text],
        >>>     start=10,  # Composite starts at t=10s in the final video
        >>>     size=(1920, 1080)
        >>>     # duration automatically calculated as max(0+5, 1+3) = 5 seconds
        >>> )
        >>> composite.set_position((100, 100))  # Move entire composite
        >>> composite.set_scale(0.5)  # Scale entire composite
        >>>
        >>> # Now background appears at t=10s and text at t=11s (10 + 1)
        >>> # Both are positioned relative to (100, 100) and scaled by 0.5
        >>>
        >>> writer = VideoWriter("output.mp4", fps=30, size=(1920, 1080))
        >>> writer.add_clip(composite)
        >>> writer.write()
    """

    def __init__(self, clips: List[GraphicClip], start: float, size: tuple[int, int], duration: Optional[float] = None, high_precision_blending: bool = False) -> None:
        """
        Create a composite clip from multiple graphic clips.

        Args:
            clips: List of GraphicClip instances to combine. Must contain at least one clip.
                   The start/duration of these clips are relative to the composite, not absolute.
            start: When the composite starts in the final video (absolute time in seconds)
            size: Dimensions (width, height) of the composite canvas
            duration: How long the composite lasts (in seconds). If None, automatically calculated
                     as the maximum end time of all child clips (relative to composite start).
            high_precision_blending: Use float32 for blending operations (default: False).
                Set to True only when compositing many layers with transparency or when
                working with subtle gradients. False uses uint8 (4x less memory, faster).

        Raises:
            ValueError: If clips list is empty
        """
        if len(clips) == 0:
            raise ValueError("CompositeClip requires at least one clip.")

        if duration is None:
            duration = max(clip.start + clip.duration for clip in clips)

        super().__init__(start, duration)
        self._clips = clips
        self._size = size
        self._high_precision_blending = high_precision_blending
        self._ef = self._create_empty_frame()

    @property
    def clips(self) -> List[GraphicClip]:
        return self._clips
    
    def get_frame(self, t_rel) -> np.ndarray:
        self._ef.clean()

        active_clips, unactive_clips = self.__get_active_and_unactive_clips(t_rel)
        background_clip = active_clips[0] if len(active_clips) > 0 else None
        remaining_active_clips = active_clips[1:]

        if background_clip:
            will_need_blending = len(remaining_active_clips) > 0
            frame = background_clip.render_as_background(
                t_rel,
                self._size[0],
                self._size[1],
                will_need_blending,
                self._high_precision_blending,
                self._ef.frame.shape[2] == 4
            )
        else:
            frame = self._ef.frame

        for clip in remaining_active_clips:
            frame = clip.render(frame, t_rel)

        # We close all unactive clips to free resources
        for unactive_clip in unactive_clips:
            unactive_clip.close()
    
        return frame

    def __get_active_and_unactive_clips(self, t_rel: float) -> tuple[list[GraphicClip], list[GraphicClip]]:
        active_clips: list[GraphicClip] = []
        unactive_clips: list[GraphicClip] = []
        for clip in self.clips:
            if 0 <= (t_rel - clip.start) < clip.duration:
                active_clips.append(clip)
            else:
                unactive_clips.append(clip)
        return active_clips, unactive_clips

    def _apply_resize(self, frame: np.ndarray) -> np.ndarray:
        interpolation = cv2.INTER_AREA if (self._target_size[0] < frame.shape[1]) else cv2.INTER_CUBIC
        return cv2.resize(frame, self._target_size, interpolation=interpolation)

    def _convert_to_mask(self, frame: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    def _create_empty_frame(self) -> empty_frame.EmptyFrame:
        return empty_frame.get(np.uint8, self._size[0], self._size[1], 3)
    
    def set_size(self, width = None, height = None) -> Self:
        super().set_size(width, height)
        self._ef = self._create_empty_frame()
        return self

    def close(self) -> None:
        for clip in self.clips:
            clip.close()
