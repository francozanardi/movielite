"""
Golden-file testing helpers.

The golden is the MP4 committed under tests/e2e/goldens/ — open it in any player to
visually verify what the test expects. Comparison is done on decoded pixels, not file
bytes: we decode both the golden and the actual output to raw yuv420p via ffmpeg and
sha256 the streams. YUV is the codec's native format, so decoding is deterministic
across ffmpeg/libx264 versions for any spec-compliant H.264 stream — portable across
environments while still catching real rendering regressions.

On failure, the actual output is dumped as _actual__<name> next to the golden for
side-by-side inspection in your player of choice.

  UPDATE_GOLDENS=1 pytest tests/e2e   # regenerate; only rewrites files whose decoded
                                      # content actually changed (keeps git diffs
                                      # clean when only encoder metadata differs)
  pytest tests/e2e                    # compare against committed goldens
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

E2E_DIR = Path(__file__).parent
FIXTURES_DIR = E2E_DIR / "fixtures"
GOLDENS_DIR = E2E_DIR / "goldens"

UPDATE_GOLDENS = os.environ.get("UPDATE_GOLDENS", "").lower() in ("1", "true", "yes")


def hash_decoded_video(path: Path) -> str:
    """Decode `path` to raw yuv420p via ffmpeg and sha256 the pixel stream."""
    proc = subprocess.Popen(
        [
            "ffmpeg", "-i", str(path),
            "-f", "rawvideo", "-pix_fmt", "yuv420p",
            "-loglevel", "error",
            "-",
        ],
        stdout=subprocess.PIPE,
    )
    h = hashlib.sha256()
    assert proc.stdout is not None
    for chunk in iter(lambda: proc.stdout.read(1 << 16), b""):
        h.update(chunk)
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed to decode {path}")
    return h.hexdigest()


def assert_matches_golden(output: Path, golden_name: str) -> None:
    """
    Compare `output` against tests/e2e/goldens/<golden_name> by decoded-pixel hash.

    - UPDATE_GOLDENS=1: overwrite the golden only if the decoded pixels actually
      differ (skips no-op writes so git stays quiet when the encoder embedded
      different container metadata but the pixels didn't change).
    - Golden missing: copy `output` into place and fail with instructions so the
      first run doesn't silently accept whatever came out.
    - Hash mismatch: copy `output` next to the golden as `_actual__<name>` for
      side-by-side visual comparison, then fail with both hashes.
    """
    output = Path(output)
    golden = GOLDENS_DIR / golden_name
    GOLDENS_DIR.mkdir(exist_ok=True)

    if UPDATE_GOLDENS:
        if not golden.exists() or hash_decoded_video(output) != hash_decoded_video(golden):
            shutil.copyfile(output, golden)
        return

    if not golden.exists():
        shutil.copyfile(output, golden)
        raise AssertionError(
            f"Golden {golden.name!r} did not exist — copied the current output into "
            f"place at {golden}. Review it visually, commit it, then re-run.\n"
            f"To (re)generate all: UPDATE_GOLDENS=1 pytest tests/e2e"
        )

    actual_hash = hash_decoded_video(output)
    expected_hash = hash_decoded_video(golden)
    if actual_hash != expected_hash:
        debug = GOLDENS_DIR / f"_actual__{golden_name}"
        shutil.copyfile(output, debug)
        raise AssertionError(
            f"Decoded-pixel mismatch for {golden_name}\n"
            f"  expected: {expected_hash}\n"
            f"  actual:   {actual_hash}\n"
            f"  actual output saved to: {debug}\n"
            f"  → open {golden.name} and _actual__{golden_name} in a player to compare.\n"
            f"If the change is intentional: UPDATE_GOLDENS=1 pytest tests/e2e"
        )
