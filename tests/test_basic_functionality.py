"""
Basic functionality tests without requiring actual media files.
"""
import numpy as np
from movielite import ImageClip


def test_image_clip_creation():
    """Test creating an ImageClip from numpy array."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :, 2] = 255  # Red channel (BGR format)

    clip = ImageClip(img, start=0, duration=5.0)

    assert clip.start == 0
    assert clip.duration == 5.0
    assert clip.size == (100, 100)


def test_clip_set_position():
    """Test setting clip position."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    clip = ImageClip(img, start=0, duration=1.0)

    # Static position
    clip.set_position((50, 100))
    pos = clip.position(0)
    assert pos == (50, 100)


def test_clip_set_opacity():
    """Test setting clip opacity."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    clip = ImageClip(img, start=0, duration=1.0)

    # Static opacity
    clip.set_opacity(0.5)
    opacity = clip.opacity(0)
    assert opacity == 0.5


def test_clip_set_scale():
    """Test setting clip scale."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    clip = ImageClip(img, start=0, duration=1.0)

    # Static scale
    clip.set_scale(2.0)
    scale = clip.scale(0)
    assert scale == 2.0


def test_clip_resize():
    """Test resizing a clip."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    clip = ImageClip(img, start=0, duration=1.0)

    clip.set_size(width=200, height=150)
    assert clip.size == (200, 150)
