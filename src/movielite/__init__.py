"""
movielite - A performance-oriented video editing library

A lightweight alternative to moviepy focused on speed and simplicity.
"""

from .core import (
    Clip,
    VideoClip,
    ProcessedVideoClip,
    ImageClip,
    AudioClip,
    TextClip,
    CompositeClip,
    VideoWriter,
    concatenate_videoclips,
    concatenate_audioclips,
    VideoQuality,
    get_logger,
    set_log_level,
)

__version__ = "0.1.0"

__all__ = [
    "Clip",
    "VideoClip",
    "ProcessedVideoClip",
    "ImageClip",
    "AudioClip",
    "TextClip",
    "CompositeClip",
    "VideoWriter",
    "concatenate_videoclips",
    "concatenate_audioclips",
    "VideoQuality",
    "get_logger",
    "set_log_level",
] 