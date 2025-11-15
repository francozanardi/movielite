import numpy as np
from .composite_clip import CompositeClip
from ..core import empty_frame

class AlphaCompositeClip(CompositeClip):
    """
    A composite clip with alpha channel (transparency) support.

    This is similar to CompositeClip but processes frames with an alpha channel (BGRA format),
    allowing for transparency in the composite output. Useful when you need to composite
    multiple clips and preserve transparency in the final result.

    PERFORMANCE NOTE: Like CompositeClip, AlphaCompositeClip should only be used when you
    need to treat multiple clips as a single unit with alpha channel support. For most use
    cases, directly adding clips to VideoWriter using add_clips() is more performant.
    Additionally, alpha channel processing has ~33% more memory overhead per frame compared
    to BGR processing.

    Use AlphaCompositeClip when:
    - You need transparency in the composite output
    - You need to apply transformations to a group of clips while preserving alpha
    - You need to use the composite as a mask or overlay with transparency

    Use VideoWriter.add_clips() or CompositeClip when:
    - You don't need alpha channel in the composite output
    - You're just compositing clips without transparency requirements

    All clip timings (start, duration) and positions within an AlphaCompositeClip are
    relative to the composite's own start time and position, just like CompositeClip.

    Example:
        >>> from movielite import ImageClip, TextClip, VideoWriter, AlphaCompositeClip
        >>> from pictex import Canvas
        >>>
        >>> # Create a composite with transparent background
        >>> background = ImageClip.from_color((0, 0, 0, 0), (800, 600), start=0, duration=5)
        >>>
        >>> # Add semi-transparent text
        >>> canvas = Canvas().font_size(60).color("white").background_color("transparent")
        >>> text = TextClip("Transparent Text", start=0, duration=5, canvas=canvas)
        >>> text.set_position((100, 100))
        >>> text.set_opacity(0.7)
        >>>
        >>> # Combine into an alpha composite
        >>> composite = AlphaCompositeClip([background, text], size=(800, 600))
        >>> composite.set_start(0)
        >>>
        >>> # Use composite as a transparent overlay on video
        >>> video = VideoClip("video.mp4")
        >>>
        >>> writer = VideoWriter("output.mp4", fps=30, size=video.size)
        >>> writer.add_clip(video)
        >>> writer.add_clip(composite)  # Composite with transparency over video
        >>> writer.write()
    """

    def _convert_to_mask(self, frame: np.ndarray) -> np.ndarray:
        return frame[:, :, 3]

    def _create_empty_frame(self) -> empty_frame.EmptyFrame:
        return empty_frame.get(np.uint8, self._size[0], self._size[1], 4)
