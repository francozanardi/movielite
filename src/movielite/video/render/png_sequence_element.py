from .media_element import MediaElement
import cv2
import numpy as np
import os
from pycaps.logger import logger

class PngSequenceElement(MediaElement):
    def __init__(self, folder_path: str, start: float, duration: float, fps: float = 30.0):
        super().__init__(start, duration)
        self._fps = fps
        self._load_frames(folder_path)
        
        if self._frames:
            h, w, _ = self._frames[0].shape
            self._size = (w, h)

    def _load_frames(self, folder_path: str):
        self._frames = []
        if not os.path.isdir(folder_path):
            logger().warning(f"Png sequence folder not found: {folder_path}")
            return

        frame_files = sorted([f for f in os.listdir(folder_path) if f.endswith('.png')])
        
        for frame_file in frame_files:
            frame_path = os.path.join(folder_path, frame_file)
            frame = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
            
            if frame is not None:
                if frame.shape[2] != 4:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                self._frames.append(frame.astype(np.float32))

        self._num_frames = len(self._frames)

    def get_frame(self, t_rel: float) -> np.ndarray:
        if not self._frames:
            return np.zeros((self._size[1], self._size[0], 4), dtype=np.float32)

        idx = int(t_rel * self._fps)
        idx = max(0, min(idx, self._num_frames - 1))
        
        return self._frames[idx].copy()
