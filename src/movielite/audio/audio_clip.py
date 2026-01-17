import numpy as np
from typing import Optional, Callable, Union, Iterator, TYPE_CHECKING
import subprocess
import inspect
from ..core import MediaClip

try:
    from typing import Self # type: ignore[attr-defined]
except ImportError:
    from typing_extensions import Self

if TYPE_CHECKING:
    from ..afx.base import AudioEffect

class AudioClip(MediaClip):
    """
    An audio clip that can be overlaid on video.

    Audio is stored as float32 in range [-1.0, 1.0].
    """

    def __init__(self, path: str, start: float = 0, duration: Optional[float] = None, volume: float = 1.0, offset: float = 0):
        """
        Create an audio clip.

        Args:
            path: Path to the audio file
            start: Start time in the composition (seconds)
            duration: Duration to use (if None, uses full audio duration)
            volume: Volume multiplier (0.0 to 1.0+)
            offset: Start offset within the audio file (seconds)
        """
        super().__init__(start, duration)

        self._path = path
        self._volume = volume
        self._offset = offset
        self._sample_transforms: list[Callable[[np.ndarray, float, int], np.ndarray]] = []
        self._has_audio = True
        self._loop = False
        self._load_metadata()

        # Calculate actual source duration
        max_available_duration = self._total_duration - offset
        if self._source_duration is None:
            self._source_duration = max_available_duration

    def _load_metadata(self) -> None:
        """
        Probe audio file metadata using ffprobe.
        If the file has no audio stream, creates a silent audio clip.
        """
        probe_cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels,duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            self._path
        ]

        try:
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            self._sample_rate = int(lines[0])
            self._channels = int(lines[1])
            self._total_duration = float(lines[2])
            self._has_audio = True

        except (subprocess.CalledProcessError, ValueError, IndexError):
            # No audio or invalid audio
            self._set_silent_defaults()

    def _set_silent_defaults(self) -> None:
        """Set defaults for silent/no audio clips"""
        self._sample_rate = 44100
        self._channels = 2
        self._total_duration = 0.0
        self._has_audio = False

    def _load_chunk_raw(self, chunk_start: float, chunk_duration: float) -> np.ndarray:
        """
        Load a specific audio chunk using ffmpeg with seeking.
        Returns raw float32 numpy array in range [-1.0, 1.0] WITHOUT effects applied.

        Args:
            chunk_start: Start time in seconds (absolute position in file)
            chunk_duration: Duration in seconds

        Returns:
            Audio samples as float32 array of shape (n_samples, n_channels)
        """
        # Return silence if no audio
        if not self._has_audio:
            num_samples = int(chunk_duration * self._sample_rate)
            return np.zeros((num_samples, self._channels), dtype=np.float32)

        # Apply looping if enabled
        if self._loop and self._total_duration > 0:
            chunk_start = chunk_start % self._total_duration

        # Don't load beyond file duration
        if chunk_start >= self._total_duration:
            return np.zeros((0, self._channels), dtype=np.float32)

        actual_duration = min(chunk_duration, self._total_duration - chunk_start)

        ffmpeg_cmd = [
            "ffmpeg",
            "-ss", str(chunk_start),  # Seek to position
            "-t", str(actual_duration),  # Duration to read from source
            "-i", self._path,
        ]

        # Build atempo filter chain for speed adjustment
        # atempo filter only supports range [0.5, 2.0], so we chain multiple filters if needed
        if self._speed != 1.0:
            atempo_filters = []
            remaining_speed = self._speed
            while remaining_speed > 2.0:
                atempo_filters.append("atempo=2.0")
                remaining_speed /= 2.0
            while remaining_speed < 0.5:
                atempo_filters.append("atempo=0.5")
                remaining_speed /= 0.5
            if remaining_speed != 1.0:
                atempo_filters.append(f"atempo={remaining_speed}")
            ffmpeg_cmd.extend(["-af", ",".join(atempo_filters)])

        ffmpeg_cmd.extend([
            "-f", "f32le",  # 32-bit float little-endian
            "-acodec", "pcm_f32le",
            "-ar", str(self._sample_rate),
            "-ac", str(self._channels),
            "-"  # Output to stdout
        ])

        try:
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=True
            )

            samples = np.frombuffer(result.stdout, dtype=np.float32)
            if self._channels > 1:
                samples = samples.reshape(-1, self._channels)
            else:
                samples = samples.reshape(-1, 1)

            return samples

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to load audio chunk from {self._path}: {e}")

    def process_chunk(self, chunk: np.ndarray, chunk_start_time: float) -> np.ndarray:
        """
        Apply volume and effects to a raw audio chunk.

        Args:
            chunk: Raw float32 samples in range [-1, 1]
            chunk_start_time: Absolute time in seconds where this chunk starts in the original file

        Returns:
            Processed float32 samples in range [-1, 1]
        """
        samples = chunk.copy()

        if self._volume != 1.0:
            samples = samples * self._volume

        for transform in self._sample_transforms:
            samples = transform(samples, chunk_start_time, self._sample_rate)

        return samples

    def iter_chunks(self, chunk_duration: float = 5.0) -> Iterator[tuple[np.ndarray, float]]:
        """
        Iterate over audio chunks sequentially.
        Each chunk is loaded on-demand and includes effects applied.

        Args:
            chunk_duration: Duration of each chunk in seconds (default: 5.0s = ~850KB for stereo 44.1kHz)

        Yields:
            Tuple of (processed_samples, chunk_start_time) where:
            - processed_samples: np.ndarray of shape (n_samples, n_channels) with float32 in [-1, 1]
            - chunk_start_time: Absolute start time of this chunk in the original file
        """
        current_time = self._offset
        end_time = self._offset + self._source_duration

        # Minimum chunk duration to avoid FFmpeg errors with very small chunks
        MIN_CHUNK_DURATION = 0.001  # 1ms

        while current_time < end_time:
            actual_chunk_duration = min(chunk_duration, end_time - current_time)
            
            if actual_chunk_duration < MIN_CHUNK_DURATION:
                break

            raw_chunk = self._load_chunk_raw(current_time, actual_chunk_duration)
            if len(raw_chunk) > 0:
                processed_chunk = self.process_chunk(raw_chunk, current_time)
                yield processed_chunk, current_time

            current_time += actual_chunk_duration

    def get_samples(self, start: float = 0, end: Optional[float] = None) -> np.ndarray:
        """
        Get audio samples as numpy array.
        This loads all requested samples into memory at once.

        For memory-efficient processing of long audio, use iter_chunks() instead.

        Args:
            start: Start time relative to this clip's offset (seconds)
            end: End time relative to this clip's offset (seconds, None = until the end)

        Returns:
            Numpy array of shape (n_samples, n_channels) with float32 values in [-1, 1]
        """
        if end is None:
            end = self._source_duration

        abs_start = self._offset + start
        abs_end = self._offset + end

        duration = abs_end - abs_start
        if duration <= 0:
            return np.zeros((0, self._channels), dtype=np.float32)

        raw_samples = self._load_chunk_raw(abs_start, duration)
        return self.process_chunk(raw_samples, abs_start)

    def add_transform(self, callback: Callable[[np.ndarray, float, int], np.ndarray]) -> Self:
        """
        Apply a custom transformation to audio samples at render time.
        Multiple transformations can be chained by calling this method multiple times.

        The callback receives:
        - samples: np.ndarray of shape (n_samples, n_channels) with float32 values in [-1, 1]
        - time: absolute time in seconds (start time of this sample chunk in the original file)
        - sample_rate: sample rate in Hz

        The callback should return transformed samples with the same shape.

        Args:
            callback: Function that takes (samples, time, sample_rate) and returns transformed samples

        Returns:
            Self for chaining

        Example:
            >>> def apply_reverb(samples, t, sr):
            >>>     # Apply custom reverb effect
            >>>     return reverb_filter(samples, sr)
            >>> audio.add_transform(apply_reverb)
        """
        self._sample_transforms.append(callback)
        return self

    def set_volume_curve(self, curve: Union[Callable[[float], float], float]) -> Self:
        """
        Set a volume curve that changes over time.

        Args:
            curve: Either a float (constant volume) or a function that takes time (seconds)
                   and returns volume multiplier (0.0 to 1.0+)

        Returns:
            Self for chaining

        Example:
            >>> # Gradual volume increase
            >>> audio.set_volume_curve(lambda t: min(1.0, t / 5.0))
        """
        curve_fn = self._save_as_function(curve)

        def volume_curve_transform(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
            n_samples = len(samples)
            result = samples.copy()

            for i in range(n_samples):
                sample_time = t + i / sr
                volume = curve_fn(sample_time)
                result[i] *= volume

            return result

        self._sample_transforms.append(volume_curve_transform)
        return self

    def _save_as_function(self, value: Union[Callable, float]) -> Callable:
        """Convert static values to time-based functions"""
        if inspect.isfunction(value):
            return value
        return lambda _t, v=value: v

    def subclip(self, start: float, end: float) -> Self:
        """
        Extract a subclip from this audio.

        Args:
            start: Start time within this clip (seconds)
            end: End time within this clip (seconds)

        Returns:
            New AudioClip instance
        """
        if start < 0 or end > self.duration or start >= end:
            raise ValueError(f"Invalid subclip range: ({start}, {end}) for clip duration {self.duration}")

        new_clip = AudioClip(
            path=self._path,
            start=self._start,
            duration=end - start,
            volume=self._volume,
            offset=self._offset + start
        )

        new_clip._sample_transforms = self._sample_transforms.copy()
        new_clip._loop = self._loop
        new_clip._speed = self._speed

        return new_clip

    def set_volume(self, volume: float) -> Self:
        """
        Set the volume of this audio clip.

        Args:
            volume: Volume multiplier (0.0 to 1.0+)

        Returns:
            Self for chaining
        """
        self._volume = volume
        return self

    def set_offset(self, offset: float) -> Self:
        """
        Set the offset within the source audio file.

        Args:
            offset: Offset in seconds (must be >= 0, where to start reading from the file)

        Returns:
            Self for chaining

        Raises:
            ValueError: If offset is negative
        """
        if offset < 0:
            raise ValueError(f"Offset cannot be negative: {offset}")
        self._offset = offset
        return self

    @property
    def path(self):
        """Path to the audio file"""
        return self._path

    @property
    def volume(self):
        """Volume multiplier (0.0 to 1.0+)"""
        return self._volume

    @property
    def offset(self):
        """Offset within the source audio file (seconds)"""
        return self._offset

    @property
    def sample_rate(self):
        """Sample rate in Hz"""
        return self._sample_rate

    @property
    def channels(self):
        """Number of audio channels (1 = mono, 2 = stereo)"""
        return self._channels

    @property
    def has_audio(self):
        """Whether this clip has actual audio (False for silent/no audio clips)"""
        return self._has_audio

    def loop(self, enabled: bool = True) -> Self:
        """
        Enable or disable looping for this audio clip.
        When enabled, the audio will restart from the beginning when it reaches the end.

        Args:
            enabled: Whether to enable looping (default: True)

        Returns:
            Self for chaining
        """
        self._loop = enabled
        return self

    def add_effect(self, effect: 'AudioEffect') -> Self:
        """
        Apply an audio effect to this clip.

        Args:
            effect: An AudioEffect instance to apply

        Returns:
            Self for chaining

        Example:
            >>> from movielite import afx
            >>> clip.add_effect(afx.FadeIn(2.0)).add_effect(afx.FadeOut(1.5))
        """
        effect.apply(self)
        return self
