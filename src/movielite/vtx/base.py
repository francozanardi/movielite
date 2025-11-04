from abc import ABC, abstractmethod
from ..core import GraphicClip

class Transition(ABC):
    """Base class for transitions between two graphic clips"""

    def _validate_clips_are_consecutive(self, clip1: GraphicClip, clip2: GraphicClip, allow_gap: bool = True) -> None:
        """
        Validate that two clips are consecutive (one after the other).

        Args:
            clip1: The first clip
            clip2: The second clip
            allow_gap: If True, allows a gap between clips. If False, requires clips to be touching or overlapping.

        Raises:
            ValueError: If clips are not in proper sequence
        """
        # Check if clip2 comes after clip1
        if clip2.start < clip1.start:
            raise ValueError(
                f"Clips are not in order. "
                f"Clip2 starts at {clip2.start}s, but Clip1 starts at {clip1.start}s. "
                f"Clip2 should start at or after Clip1."
            )

        # If gaps are not allowed, ensure clips are touching or overlapping
        if not allow_gap and clip2.start > clip1.end:
            gap = clip2.start - clip1.end
            raise ValueError(
                f"Clips have a gap between them. "
                f"Clip1 ends at {clip1.end}s, but Clip2 starts at {clip2.start}s (gap: {gap}s). "
                f"This transition requires clips to be consecutive without gaps."
            )

    def _validate_clips_have_overlap(self, clip1: GraphicClip, clip2: GraphicClip, min_overlap: float) -> None:
        """
        Validate that two clips have sufficient overlap for the transition.

        Args:
            clip1: The first clip
            clip2: The second clip
            min_overlap: Minimum required overlap duration in seconds

        Raises:
            ValueError: If clips don't overlap sufficiently
        """
        # Check if clips overlap at all
        if clip2.start >= clip1.end:
            raise ValueError(
                f"Clips do not overlap. "
                f"Clip1 ends at {clip1.end}s, but Clip2 starts at {clip2.start}s. "
                f"This transition requires an overlap of at least {min_overlap}s."
            )

        # Check if the overlap is sufficient
        overlap = clip1.end - clip2.start
        if overlap < min_overlap:
            raise ValueError(
                f"Insufficient overlap for transition. "
                f"Required overlap: {min_overlap}s, actual overlap: {overlap:.2f}s. "
                f"Clip1: [{clip1.start}s - {clip1.end}s], Clip2: [{clip2.start}s - {clip2.end}s]"
            )

    @abstractmethod
    def apply(self, clip1: GraphicClip, clip2: GraphicClip) -> None:
        """
        Apply transition between two clips by modifying their properties.

        Args:
            clip1: The outgoing clip (typically fades out)
            clip2: The incoming clip (typically fades in)
        """
        pass
