from abc import ABC, abstractmethod
import numpy as np


class VideoReader(ABC):
    """Strategy interface for video decoders.

    Readers are stateful: they own a decoder handle and a cache of the last
    frame delivered, so consecutive calls to get_frame() with the same or
    nearby indices are cheap.

    A reader is bound to a single output pixel format (BGR or BGRA), chosen
    at construction. Consumers can check channels to know what shape
    get_frame() returns without having to inspect the concrete class.
    """

    @property
    @abstractmethod
    def size(self) -> tuple[int, int]:
        """(width, height) in pixels."""

    @property
    @abstractmethod
    def fps(self) -> float:
        ...

    @property
    @abstractmethod
    def total_frames(self) -> int:
        ...

    @property
    @abstractmethod
    def channels(self) -> int:
        """3 for BGR, 4 for BGRA."""

    @abstractmethod
    def get_frame(self, frame_idx: int) -> np.ndarray:
        """Return the frame at frame_idx, clipped to [0, total_frames-1]."""

    @abstractmethod
    def close(self) -> None:
        ...
