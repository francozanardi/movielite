import numpy as np

_empty_frames = {}
class EmptyFrame:
    def __init__(self, frame: np.ndarray):
        self.frame: np.ndarray = frame
        self._is_dirty: bool = False

    def clean(self):
        if not self._is_dirty:
            return
        
        self.frame.fill(0)
        self._is_dirty = False
    
    def mark_as_dirty(self):
        self._is_dirty = True

def get(dtype: np.dtype, width: int, height: int, components: int) -> EmptyFrame:
    key = str(dtype) + "_" + str(components) + "_" + str(width) + "_" + str(height)
    if key not in _empty_frames:
        empty_frame = np.zeros((height, width, components), dtype=dtype)
        _empty_frames[key] = EmptyFrame(empty_frame)
    
    return _empty_frames[key]

def clean_all():
    for empty_frame in _empty_frames.values():
        empty_frame.clean()
