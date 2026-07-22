"""
E2E fixtures and gating.

These tests only make sense inside the pinned Dockerfile.test container: byte-exact
comparison requires the same ffmpeg/libx264 build that produced the goldens. On any
other host the tests skip loudly rather than clobber goldens with mismatched bytes.

Set MOVIELITE_E2E=1 to force-run outside Docker (accepts the byte-mismatch risk).
"""
import os
import subprocess
from pathlib import Path

import pytest

from .helpers import E2E_DIR, FIXTURES_DIR, UPDATE_GOLDENS

_IN_DOCKER = Path("/.dockerenv").exists()
_FORCE = os.environ.get("MOVIELITE_E2E", "").lower() in ("1", "true", "yes")
_E2E_ROOT = E2E_DIR.resolve()


def pytest_collection_modifyitems(config, items):
    # This hook fires for the WHOLE session, not just this directory —
    # filter to items under tests/e2e/ so we don't skip unrelated unit tests.
    if _IN_DOCKER or _FORCE:
        return
    skip = pytest.mark.skip(
        reason="e2e tests require the pinned Dockerfile.test container "
        "(set MOVIELITE_E2E=1 to override, at your own risk)"
    )
    for item in items:
        if Path(item.fspath).resolve().is_relative_to(_E2E_ROOT):
            item.add_marker(skip)


def _generate_bg_fixture(path: Path) -> None:
    """Generate tests/e2e/fixtures/bg.mp4 via ffmpeg testsrc2 — 128x72 @ 15fps, 2s.

    Deterministic within a given ffmpeg build, so committing this file and
    regenerating it in the same container both produce identical bytes.
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
        if not (UPDATE_GOLDENS or _FORCE):
            pytest.fail(
                f"Input fixture missing: {path}\n"
                f"Run with UPDATE_GOLDENS=1 (inside Docker) to auto-generate, "
                f"then commit tests/e2e/fixtures/bg.mp4"
            )
        _generate_bg_fixture(path)
    return path


@pytest.fixture
def output_path(tmp_path) -> Path:
    return tmp_path / "output.mp4"
