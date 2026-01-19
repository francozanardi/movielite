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
from .composite import CompositeClip, AlphaCompositeClip
from .enums import VideoQuality
from .logger import get_logger, set_log_level
from . import vfx, afx, vtx

__version__ = "0.2.2"

__all__ = [
    "MediaClip",
    "GraphicClip",
    "VideoClip",
    "AlphaVideoClip",
    "ImageClip",
    "AudioClip",
    "TextClip",
    "CompositeClip",
    "AlphaCompositeClip",
    "VideoWriter",
    "VideoQuality",
    "get_logger",
    "set_log_level",
    "vfx",
    "afx",
    "vtx",
]
