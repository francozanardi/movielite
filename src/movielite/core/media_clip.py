from abc import ABC
from typing import Optional

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
            duration: Duration in seconds
        """
        self._start = start
        self._duration = duration

    @property
    def start(self):
        """Start time of the clip in the composition (seconds)"""
        return self._start

    @property
    def duration(self):
        """Duration of the clip (seconds)"""
        return self._duration

    @property
    def end(self):
        """End time of the clip in the composition (seconds)"""
        return self._start + self._duration

    def set_start(self, start: float) -> 'MediaClip':
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

    def set_duration(self, duration: float) -> 'MediaClip':
        """
        Set the duration of this clip.

        Args:
            duration: Duration in seconds (must be > 0)

        Returns:
            Self for chaining

        Raises:
            ValueError: If duration is not positive
        """
        if duration <= 0:
            raise ValueError(f"Duration must be positive: {duration}")
        self._duration = duration
        return self

    def set_end(self, end: float) -> 'MediaClip':
        """
        Set the end time of this clip in the composition.
        Adjusts duration to match: duration = end - start

        Args:
            end: End time in seconds (must be > start)

        Returns:
            Self for chaining

        Raises:
            ValueError: If end is not greater than start
        """
        if end <= self._start:
            raise ValueError(f"End time ({end}) must be greater than start time ({self._start})")
        self._duration = end - self._start
        return self
