"""Regression tests for VideoClip reader selection (issue #11).

The bug: cv2.VideoCapture opens an AV1 file, reports valid metadata, but
returns (False, None) from every read() call. It failed silently, so users
got a rendered video full of black frames instead of an error.

The fix probes cv2 with a first-frame decode; on failure we transparently
fall back to an ffmpeg subprocess reader. These tests lock that in.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from movielite.video import VideoClip
from movielite.video.readers import Cv2Reader, FfmpegReader


def _ffmpeg_has_encoder(name: str) -> bool:
    if shutil.which("ffmpeg") is None:
        return False
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True, text=True, check=True,
    ).stdout
    return any(line.strip().startswith("V") and name in line for line in out.splitlines())


@pytest.fixture(scope="session")
def av1_fixture(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generate a small AV1 clip with libsvtav1 (Ubuntu 22.04+ ffmpeg ships it).

    testsrc2 produces a deterministic colored pattern, so mean() is well above
    zero and we can distinguish a real decode from cv2's silent zero-frames.
    """
    if not _ffmpeg_has_encoder("libsvtav1"):
        pytest.skip("libsvtav1 not available in this ffmpeg build")

    path = tmp_path_factory.mktemp("av1") / "sample.mp4"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi",
            "-i", "testsrc2=size=128x72:rate=15:duration=1",
            "-c:v", "libsvtav1",
            "-preset", "8",
            "-crf", "35",
            "-pix_fmt", "yuv420p",
            "-an",
            str(path),
        ],
        check=True,
    )
    return path


def test_av1_falls_back_to_ffmpeg_reader(av1_fixture: Path):
    """Regression for #11: cv2 can't decode AV1, factory must fall back to ffmpeg."""
    clip = VideoClip(str(av1_fixture), start=0, duration=1)
    try:
        assert isinstance(clip._reader, FfmpegReader), (
            f"Expected FfmpegReader fallback for AV1, got {type(clip._reader).__name__}. "
            "This means either cv2 gained AV1 support (great — update this test) or "
            "the probe/fallback logic broke."
        )
    finally:
        clip.close()


def test_av1_decodes_non_empty_frames(av1_fixture: Path):
    """The core symptom of #11 was silently-black frames. Prove they decode now."""
    clip = VideoClip(str(av1_fixture), start=0, duration=1)
    try:
        frame = clip.get_frame(0)
        assert frame.shape == (72, 128, 3), f"unexpected frame shape {frame.shape}"
        assert frame.mean() > 0, "AV1 frame decoded as all zeros — the #11 bug is back"
    finally:
        clip.close()


def test_h264_still_uses_cv2_reader():
    """Guardrail: don't accidentally push everything to the slow ffmpeg path.

    Uses tests/e2e/fixtures/bg.mp4 (a small H.264 clip already in the repo).
    If this test starts failing, someone changed the factory to always return
    FfmpegReader — cv2 is 10-20x faster on supported codecs, don't regress that.
    """
    bg = Path(__file__).parent / "e2e" / "fixtures" / "bg.mp4"
    if not bg.exists():
        pytest.skip(f"{bg} not present")

    clip = VideoClip(str(bg), start=0, duration=1)
    try:
        assert isinstance(clip._reader, Cv2Reader), (
            f"Expected Cv2Reader for H.264, got {type(clip._reader).__name__}"
        )
    finally:
        clip.close()
