"""E2E fixtures. See helpers.py for the comparison strategy."""
import subprocess
from pathlib import Path

import pytest

from .helpers import E2EOutput, FIXTURES_DIR, install_frame_capture


def _generate_bg_fixture(path: Path) -> None:
    """testsrc2 128x72 @ 15fps, 2s. Only used to (re)create tests/e2e/fixtures/bg.mp4
    if it's missing — normally the file is committed so every run reads the same
    H.264 stream and movielite decodes identical frames.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "testsrc2=size=128x72:rate=15:duration=2",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(path),
            "-loglevel", "error",
            "-hide_banner",
        ],
        check=True,
    )


@pytest.fixture(scope="session")
def bg_video() -> Path:
    path = FIXTURES_DIR / "bg.mp4"
    if not path.exists():
        _generate_bg_fixture(path)
    return path


@pytest.fixture
def output(monkeypatch, tmp_path) -> E2EOutput:
    """Bundles the MP4 output path (for VideoWriter) and the raw-frame capture path
    (populated transparently via monkeypatch on subprocess.Popen)."""
    mp4 = tmp_path / "output.mp4"
    raw = tmp_path / "raw_frames.bin"
    install_frame_capture(monkeypatch, raw)
    return E2EOutput(mp4=mp4, raw=raw)
