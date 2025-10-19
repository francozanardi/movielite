import numpy as np
from typing import List, Tuple
from .clip import Clip

class CompositeClip(Clip):
    """
    A composite clip that combines multiple clips together.

    This is useful for creating complex compositions where multiple
    video, image, or text clips are layered on top of each other.
    """

    def __init__(
            self,
            clips: List[Clip],
            start: float = 0,
            duration: float = None,
            size: Tuple[int, int] = (1920, 1080),
        ):
        """
        Create a composite clip from multiple clips.

        Args:
            clips: List of Clip instances to compose
            start: Start time in the composition (seconds)
            duration: Duration of the composite (if None, uses max end time of clips)
            size: Size of the composite canvas (width, height)
        """
        if duration is None:
            # Calculate duration from the maximum end time of all clips
            if clips:
                duration = max(clip.end for clip in clips)
            else:
                duration = 0

        super().__init__(start, duration)
        self._clips = clips
        self._size = size

    def get_frame(self, t_rel: float) -> np.ndarray:
        """
        Compose all clips at the given relative time.

        Args:
            t_rel: Relative time within this composite

        Returns:
            Composed frame with all clips rendered
        """
        # Create transparent background
        frame = np.zeros((self._size[1], self._size[0], 4), dtype=np.float32)

        # Render each clip onto the frame
        for clip in self._clips:
            frame = clip.render(frame, t_rel)

        return frame

    def add_clip(self, clip: Clip) -> 'CompositeClip':
        """
        Add a clip to this composite.

        Args:
            clip: Clip to add

        Returns:
            Self for chaining
        """
        self._clips.append(clip)

        # Update duration if necessary
        if clip.end > self._duration:
            self._duration = clip.end

        return self
