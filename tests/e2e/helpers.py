"""
Golden-file testing helpers.

Comparison is done on the raw BGR frames movielite hands to ffmpeg's stdin, BEFORE
they get encoded. We tee ffmpeg's stdin into a capture file during the test run and
sha256 that. The hash is independent of the libx264 version — any encoder-level
difference between environments is invisible to the comparison, which is exactly
what we want: we're testing movielite's rendering, not ffmpeg's encoding.

The output MP4 is still written normally and committed as the golden, purely so
humans can open it in a player to see what the test expects. On failure, the
actual MP4 is dumped next to the golden for side-by-side inspection.

Layout:
  tests/e2e/goldens/<name>.mp4   ← human-viewable reference
  tests/e2e/goldens/hashes.json  ← what the tests actually compare against

  UPDATE_GOLDENS=1 pytest tests/e2e   # regen; MP4 is only rewritten when its
                                      # pre-encoder hash actually changed
  pytest tests/e2e                    # compare captured bytes vs stored hash

Note: only works with `processes=1` in VideoWriter.write() — with multiprocessing,
the ffmpeg subprocess spawns in worker processes that don't see the monkeypatch.
"""
import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

E2E_DIR = Path(__file__).parent
FIXTURES_DIR = E2E_DIR / "fixtures"
GOLDENS_DIR = E2E_DIR / "goldens"
HASHES_FILE = GOLDENS_DIR / "hashes.json"

UPDATE_GOLDENS = os.environ.get("UPDATE_GOLDENS", "").lower() in ("1", "true", "yes")


@dataclass
class E2EOutput:
    """Bundle produced by the `output` fixture. Pass `.mp4` to VideoWriter; the
    monkeypatch fills `.raw` transparently while movielite writes the MP4."""
    mp4: Path
    raw: Path


class _StdinTee:
    """File-like wrapper: every .write() goes to both the real ffmpeg stdin and a
    capture file. Passthrough of .close() and .flush() so movielite's writer
    lifecycle (which closes stdin then waits) still works."""

    def __init__(self, real, capture):
        self._real = real
        self._capture = capture

    def write(self, data):
        self._capture.write(data)
        return self._real.write(data)

    def close(self):
        try:
            self._capture.close()
        finally:
            return self._real.close()

    def flush(self):
        return self._real.flush()


def install_frame_capture(monkeypatch, capture_path: Path) -> None:
    """Wrap subprocess.Popen so any 'ffmpeg -i pipe:0 …' call tees stdin bytes to
    `capture_path`. That's how movielite's writer invokes its encoder; audio muxing
    passes files instead of pipe:0, so it's left alone.
    """
    real_popen = subprocess.Popen

    def wrapped_popen(cmd, *args, **kwargs):
        proc = real_popen(cmd, *args, **kwargs)
        if (
            isinstance(cmd, list)
            and cmd
            and cmd[0] == "ffmpeg"
            and "-i" in cmd
            and cmd[cmd.index("-i") + 1] == "pipe:0"
            and proc.stdin is not None
        ):
            capture = open(capture_path, "ab")
            proc.stdin = _StdinTee(proc.stdin, capture)
        return proc

    monkeypatch.setattr(subprocess, "Popen", wrapped_popen)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_hashes() -> dict:
    if not HASHES_FILE.exists():
        return {}
    return json.loads(HASHES_FILE.read_text())


def _save_hashes(hashes: dict) -> None:
    GOLDENS_DIR.mkdir(exist_ok=True)
    HASHES_FILE.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")


def assert_matches_golden(output: E2EOutput, golden_name: str) -> None:
    """Compare the pre-encoder pixel bytes movielite produced against the stored
    hash for `golden_name`. On the update path, also refresh the golden MP4 so
    the human-viewable reference stays in sync with the hash.
    """
    actual_hash = _sha256_file(output.raw)
    hashes = _load_hashes()
    golden_mp4 = GOLDENS_DIR / golden_name
    GOLDENS_DIR.mkdir(exist_ok=True)

    if UPDATE_GOLDENS:
        hash_changed = hashes.get(golden_name) != actual_hash
        if hash_changed:
            hashes[golden_name] = actual_hash
            _save_hashes(hashes)
        if hash_changed or not golden_mp4.exists():
            shutil.copyfile(output.mp4, golden_mp4)
        return

    if golden_name not in hashes:
        hashes[golden_name] = actual_hash
        _save_hashes(hashes)
        shutil.copyfile(output.mp4, golden_mp4)
        raise AssertionError(
            f"No golden for {golden_name!r}. Wrote current output to {golden_mp4} "
            f"and its pre-encoder hash to {HASHES_FILE}. Review the video, commit, "
            f"then re-run.\n"
            f"To regen all: UPDATE_GOLDENS=1 pytest tests/e2e"
        )

    expected_hash = hashes[golden_name]
    if actual_hash != expected_hash:
        debug = GOLDENS_DIR / f"_actual__{golden_name}"
        shutil.copyfile(output.mp4, debug)
        raise AssertionError(
            f"Pre-encoder pixel hash mismatch for {golden_name}\n"
            f"  expected: {expected_hash}\n"
            f"  actual:   {actual_hash}\n"
            f"  actual output saved to: {debug}\n"
            f"  → play {golden_mp4.name} and _actual__{golden_name} side by side.\n"
            f"If the change is intentional: UPDATE_GOLDENS=1 pytest tests/e2e"
        )
