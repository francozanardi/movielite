import cv2
import numpy as np
import os
from typing import Optional
from ..core import GraphicClip
from ..audio import AudioClip
from ..logger import get_logger

try:
    from typing import Self # type: ignore[attr-defined]
except ImportError:
    from typing_extensions import Self

class VideoClip(GraphicClip):
    """
    A video clip that loads and processes frames in BGR format (no alpha channel).

    This class is optimized for videos without transparency. For videos with alpha channel
    (transparency), use AlphaVideoClip instead. Note that AlphaVideoClip has a performance
    penalty (~33% more memory per frame) due to the additional alpha channel.
    """

    def __init__(self, path: str, start: float = 0, duration: Optional[float] = None, offset: float = 0):
        """
        Load a video clip for frame-level processing.

        Args:
            path: Path to the video file
            start: Start time in the composition (seconds)
            duration: Duration to use from the video (if None, uses full video duration)
            offset: Start offset within the video file (seconds)
        """
        super().__init__(start, duration)

        ext = os.path.splitext(path)[1].lower()
        if ext not in self._get_supported_video_file_extensions():
            raise ValueError(f"Unsupported video format: {ext}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Video file not found: {path}")

        self._path = path
        self._offset = offset

        self._load_metadata(path)

        # Determine actual source duration
        video_duration = self._total_frames / self._fps
        if self._source_duration is None:
            self._source_duration = video_duration - offset

        self._audio_clip = AudioClip(
            path=self._path,
            start=self._start,
            duration=self._source_duration,  # Pass source duration to audio
            offset=self._offset
        )

        # Video reading state
        self._cap = None
        self._last_frame_idx = -1
        self._last_frame = None
        self._loop = False
    
    def _get_supported_video_file_extensions(self) -> list[str]:
        return ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.webp', '.gif']

    def get_frame(self, t_rel: float) -> np.ndarray:
        """Get frame at relative time within this clip"""
        actual_time = t_rel + self._offset
        if self._loop:
            video_duration = self._total_frames / self._fps
            actual_time = (actual_time % video_duration) if video_duration > 0 else actual_time

        target_frame_idx = int(actual_time * self._fps)
        target_frame_idx = max(0, min(target_frame_idx, self._total_frames - 1))

        if self._cap is None:
            self._cap = cv2.VideoCapture(self._path)
            self._last_frame_idx = -1
            get_logger().debug(f"ProcessedVideoClip: Opened video capture for {self._path}")

        if target_frame_idx == self._last_frame_idx and self._last_frame is not None:
            return self._last_frame
        
        if target_frame_idx < self._last_frame_idx or target_frame_idx - self._last_frame_idx > 5:
            # Need to seek (slower, but necessary for random access)
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_idx)
            ret, frame = self._cap.read()
            if not ret:
                get_logger().warning(f"Failed to read frame {target_frame_idx} from {self._path}")
                return np.zeros((self._size[1], self._size[0], 3), dtype=np.uint8)
            
            self._last_frame_idx = target_frame_idx
            self._last_frame = frame
            return frame
        
        current_frame_idx = self._last_frame_idx
        while current_frame_idx < target_frame_idx:
            ret, frame = self._cap.read()
            if not ret:
                get_logger().warning(f"Failed to read frame {target_frame_idx} from {self._path}")
                frame = np.zeros((self._size[1], self._size[0], 3), dtype=np.uint8)
            
            current_frame_idx = current_frame_idx + 1
        
        self._last_frame_idx = current_frame_idx
        self._last_frame = frame
        return frame

    def _apply_resize(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame (happens every frame for videos)"""
        interpolation = cv2.INTER_AREA if (self._target_size[0] < frame.shape[1]) else cv2.INTER_CUBIC
        return cv2.resize(frame, self._target_size, interpolation=interpolation)

    def _convert_to_mask(self, frame: np.ndarray) -> np.ndarray:
        """Convert video frame to 2D mask (0-255 uint8)"""
        if frame.shape[2] == 4:
            # Use alpha channel
            mask = frame[:, :, 3]
        else:
            # Convert to grayscale
            mask = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return mask

    def close(self):
        """Close the video file"""
        super().close()
        if hasattr(self, '_cap') and self._cap is not None:
            self._cap.release()
            self._cap = None
        if hasattr(self, '_last_frame_idx'):
            self._last_frame_idx = -1
        if hasattr(self, '_last_frame'):
            self._last_frame = None

    def subclip(self, start: float, end: float) -> Self:
        """
        Extract a subclip from this video.

        Args:
            start: Start time within this clip (seconds)
            end: End time within this clip (seconds)

        Returns:
            New ProcessedVideoClip instance
        """
        if start < 0 or end > self.duration or start >= end:
            raise ValueError(f"Invalid subclip range: ({start}, {end}) for clip duration {self.duration}")

        new_clip = self.__new__(type(self))
        new_clip._path = self._path
        new_clip._fps = self._fps
        new_clip._size = self._size
        new_clip._total_frames = self._total_frames
        new_clip._offset = self._offset + start
        new_clip._start = self._start
        new_clip._source_duration = (end - start) * self._speed
        new_clip._position = self._position
        new_clip._opacity = self._opacity
        new_clip._scale = self._scale
        new_clip._target_size = self._target_size
        new_clip._frame_transforms = self._frame_transforms.copy()
        new_clip._pixel_transforms = self._pixel_transforms.copy()
        new_clip._mask = self._mask
        new_clip._cap = None
        new_clip._last_frame_idx = -1
        new_clip._last_frame = None
        new_clip._loop = self._loop
        new_clip._speed = self._speed

        # Create audio clip for the subclip
        new_clip._audio_clip = self._audio_clip.subclip(start, end)

        return new_clip

    def _load_metadata(self, path: str) -> None:
        """Load video metadata using cv2.VideoCapture"""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video file: {path}")

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._fps = cap.get(cv2.CAP_PROP_FPS)
        self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self._fps <= 0 or w <= 0 or h <= 0 or self._total_frames <= 0:
            cap.release()
            raise RuntimeError(f"Could not read valid properties from video: {path}")

        self._size = (w, h)

        get_logger().debug(f"ProcessedVideoClip loaded: {path}, size=({w}, {h}), fps={self._fps}, frames={self._total_frames}")
        cap.release()

    @property
    def fps(self):
        """Get the frames per second of this video"""
        return self._fps

    @property
    def audio(self) -> AudioClip:
        """
        Get the audio track of this video clip.

        The audio track is synchronized with the video's start, duration, and offset.
        You can modify the audio independently (e.g., fade in/out, volume adjustments).

        Returns:
            AudioClip associated with this video

        Example:
            >>> video = VideoClip("video.mp4", start=0, duration=10)
            >>> video.audio.set_volume(0.5)
        """
        return self._audio_clip

    def set_start(self, start: float) -> Self:
        """
        Set the start time of this clip in the composition.
        Also updates the audio track's start time.

        Args:
            start: Start time in seconds

        Returns:
            Self for chaining
        """
        self._start = start
        self._audio_clip._start = start
        return self

    def set_duration(self, duration: float) -> Self:
        """
        Set the duration of this clip.
        Also updates the audio track's duration.

        Args:
            duration: Duration in seconds

        Returns:
            Self for chaining
        """
        super().set_duration(duration)
        self._audio_clip._source_duration = self._source_duration
        return self

    def set_offset(self, offset: float) -> Self:
        """
        Set the offset within the source video file.
        Also updates the audio track's offset.

        Args:
            offset: Offset in seconds

        Returns:
            Self for chaining
        """
        self._offset = offset
        self._audio_clip._offset = offset
        return self

    def set_end(self, end: float) -> Self:
        """
        Set the end time of this clip in the composition.
        Also updates the audio track's end time.
        Adjusts duration to match, accounting for speed.

        Args:
            end: End time in seconds

        Returns:
            Self for chaining
        """
        super().set_end(end)
        self._audio_clip._source_duration = self._source_duration
        return self

    def set_speed(self, speed: float) -> Self:
        """
        Set the playback speed of this video clip.
        Also updates the audio track's speed.

        Args:
            speed: Speed multiplier (must be > 0)
                  - 1.0 = normal speed
                  - 2.0 = twice as fast
                  - 0.5 = half speed

        Returns:
            Self for chaining
        """
        super().set_speed(speed)
        self._audio_clip._speed = speed
        return self

    def loop(self, enabled: bool = True) -> Self:
        """
        Enable or disable looping for this video clip.
        When enabled, the video will restart from the beginning when it reaches the end.
        Also applies looping to the audio track.

        Args:
            enabled: Whether to enable looping (default: True)

        Returns:
            Self for chaining
        """
        self._loop = enabled
        self._audio_clip._loop = enabled
        return self
