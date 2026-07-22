"""
Black-box e2e tests for core video features.

Each test builds a small composition, renders to MP4, and asserts the pre-encoder
pixel bytes match the committed golden. Kept to the core video surface — subclip,
position, opacity, scale, speed — plus a baseline no-op passthrough.

Everything uses processes=1 (required by the frame-capture monkeypatch — see
helpers.py) and VideoQuality.MIDDLE for determinism of the visible MP4 golden.
"""
from movielite import VideoClip, VideoQuality, VideoWriter

from .helpers import assert_matches_golden


_FPS = 15
_SIZE = (128, 72)


def _write(clip, mp4_path):
    writer = VideoWriter(str(mp4_path), fps=_FPS, size=_SIZE)
    writer.add_clip(clip)
    writer.write(processes=1, video_quality=VideoQuality.MIDDLE)


def test_passthrough(bg_video, output):
    clip = VideoClip(str(bg_video))
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "passthrough.mp4")


def test_subclip(bg_video, output):
    clip = VideoClip(str(bg_video)).subclip(0.5, 1.5)
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "subclip.mp4")


def test_position_static(bg_video, output):
    clip = VideoClip(str(bg_video)).set_position((20, 10))
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "position_static.mp4")


def test_position_animated(bg_video, output):
    clip = VideoClip(str(bg_video)).set_position(lambda t: (int(30 * t), int(15 * t)))
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "position_animated.mp4")


def test_opacity_static(bg_video, output):
    clip = VideoClip(str(bg_video)).set_opacity(0.5)
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "opacity_static.mp4")


def test_opacity_animated(bg_video, output):
    clip = VideoClip(str(bg_video)).set_opacity(lambda t: t / 2.0)
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "opacity_animated.mp4")


def test_scale_down(bg_video, output):
    clip = VideoClip(str(bg_video)).set_scale(0.5)
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "scale_down.mp4")


def test_scale_animated(bg_video, output):
    clip = VideoClip(str(bg_video)).set_scale(lambda t: 0.5 + 0.25 * t)
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "scale_animated.mp4")


def test_speed_fast(bg_video, output):
    clip = VideoClip(str(bg_video)).set_speed(2.0)
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "speed_fast.mp4")


def test_speed_slow(bg_video, output):
    clip = VideoClip(str(bg_video)).set_speed(0.5)
    _write(clip, output.mp4)
    clip.close()
    assert_matches_golden(output, "speed_slow.mp4")
