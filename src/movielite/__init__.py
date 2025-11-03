"""
movielite - A performance-oriented video editing library

A lightweight alternative to moviepy focused on speed and simplicity.
"""

from .bootstrap import check_dependencies

check_dependencies()

from .core import (
    MediaClip,
    GraphicClip,
    VideoWriter,
)
from .audio import AudioClip
from .video import VideoClip, AlphaVideoClip
from .image import ImageClip, TextClip
from .enums import VideoQuality
from .logger import get_logger, set_log_level

__version__ = "0.1.0"

__all__ = [
    "MediaClip",
    "GraphicClip",
    "VideoClip",
    "AlphaVideoClip",
    "ImageClip",
    "AudioClip",
    "TextClip",
    "VideoWriter",
    "VideoQuality",
    "get_logger",
    "set_log_level",
]
