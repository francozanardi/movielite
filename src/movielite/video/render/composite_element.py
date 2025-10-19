from .media_element import MediaElement
import numpy as np
from typing import List, Tuple

class CompositeElement(MediaElement):
    def __init__(
            self,
            elements: List[MediaElement],
            start: float,
            duration: float,
            size: Tuple[int, int],
        ):
        super().__init__(start, duration)
        self._elements = elements
        self._size = size

    def get_frame(self, t_rel: float) -> np.ndarray:
        frame = np.zeros((self._size[1], self._size[0], 4), dtype=np.float32)
        for element in self._elements:
            frame = element.render(frame, t_rel)
        return frame
