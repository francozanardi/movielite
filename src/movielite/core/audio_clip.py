from typing import Optional

class AudioClip:
    """
    An audio clip that can be overlaid on video.

    Audio clips are handled separately from visual clips since they don't render frames.
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
        self._path = path
        self._start = start
        self._volume = volume
        self._offset = offset
        self._duration = duration

        # Load duration if not provided
        if self._duration is None:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(path)
            total_duration_sec = len(audio) / 1000.0
            self._duration = total_duration_sec - offset

    def subclip(self, start: float, end: float) -> 'AudioClip':
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

        return AudioClip(
            path=self._path,
            start=0,
            duration=end - start,
            volume=self._volume,
            offset=self._offset + start
        )

    def set_volume(self, volume: float) -> 'AudioClip':
        """
        Set the volume of this audio clip.

        Args:
            volume: Volume multiplier (0.0 to 1.0+)

        Returns:
            Self for chaining
        """
        self._volume = volume
        return self

    @property
    def path(self):
        return self._path

    @property
    def start(self):
        return self._start

    @property
    def duration(self):
        return self._duration

    @property
    def end(self):
        return self._start + self._duration

    @property
    def volume(self):
        return self._volume

    @property
    def offset(self):
        return self._offset
