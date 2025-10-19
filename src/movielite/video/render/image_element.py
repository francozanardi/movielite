from .media_element import MediaElement
import cv2
import numpy as np
from typing import Union

class ImageElement(MediaElement):
    def __init__(self, source: Union[str, np.ndarray], start: float, duration: float):
        super().__init__(start, duration)
        if isinstance(source, str):
            img = cv2.imread(source, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise FileNotFoundError(f"Image not found: {source}")
            if img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        else:
            img = cv2.cvtColor(source, cv2.COLOR_RGBA2BGRA) if source.shape[2] == 4 else cv2.cvtColor(source, cv2.COLOR_RGB2BGRA)

        self._image = img.astype(np.float32)
        self._size = self._image.shape[1], self._image.shape[0]

    def get_frame(self, t_rel: float) -> np.ndarray:
        # TODO: we shouldn't copy each frame... it should be copied only if needed
        return self._image.copy()
