from abc import ABC

try:
    from typing import Self # type: ignore[attr-defined]
except ImportError:
    from typing_extensions import Self

class MediaClip(ABC):
    """
    Base class for all media clips (visual and audio).

    Provides common timing properties and setters that all media clips share.
    """

    def __init__(self, start: float, duration: float):
        """
        Initialize a MediaClip.

        Args:
            start: Start time in seconds
            duration: Duration in seconds (how much source content to use)
        """
        self._start = start
        self._source_duration = duration
        self._speed = 1.0

    @property
    def start(self):
        """Start time of the clip in the composition (seconds)"""
        return self._start

    @property
    def duration(self):
        """
        Duration of the clip in the timeline (seconds).
        
        This accounts for playback speed:
        - 20s of source at speed=2.0 → 10s in timeline
        - 20s of source at speed=0.5 → 40s in timeline
        """
        return self._source_duration / self._speed

    @property
    def end(self):
        """
        End time of the clip in the composition (seconds).
        
        Simply: start + duration (where duration already accounts for speed)
        """
        return self._start + self.duration

    @property
    def speed(self):
        """Playback speed multiplier (1.0 = normal, 2.0 = 2x faster, 0.5 = half speed)"""
        return self._speed

    def set_start(self, start: float) -> Self:
        """
        Set the start time of this clip in the composition.

        Args:
            start: Start time in seconds (must be >= 0)

        Returns:
            Self for chaining

        Raises:
            ValueError: If start is negative
        """
        if start < 0:
            raise ValueError(f"Start time cannot be negative: {start}")
        self._start = start
        return self

    def set_duration(self, duration: float) -> Self:
        """
        Set the duration of this clip in the timeline.

        Args:
            duration: Duration in seconds in the timeline (must be > 0)

        Returns:
            Self for chaining

        Raises:
            ValueError: If duration is not positive
        """
        if duration <= 0:
            raise ValueError(f"Duration must be positive: {duration}")
        self._source_duration = duration * self._speed
        return self

    def set_speed(self, speed: float) -> Self:
        """
        Set the playback speed of this clip.

        Args:
            speed: Speed multiplier (must be > 0)
                  - 1.0 = normal speed
                  - 2.0 = twice as fast
                  - 0.5 = half speed

        Returns:
            Self for chaining

        Raises:
            ValueError: If speed is not positive
        """
        if speed <= 0:
            raise ValueError(f"Speed must be positive: {speed}")
        self._speed = speed
        return self

    def set_end(self, end: float) -> Self:
        """
        Set the end time of this clip in the composition.
        Adjusts the timeline duration to match.
        
        Args:
            end: End time in seconds (must be > start)

        Returns:
            Self for chaining

        Raises:
            ValueError: If end is not greater than start
        """
        if end <= self._start:
            raise ValueError(f"End time ({end}) must be greater than start time ({self._start})")
        timeline_duration = end - self._start
        self._source_duration = timeline_duration * self._speed
        return self
