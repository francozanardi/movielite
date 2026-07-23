"""Generate benchmark fixtures in multiple codecs from tests/e2e/fixtures/bg.mp4.

Produces videos with identical content but different codecs, so the
benchmark isolates the effect of the decoder from resolution/content:

    fixtures/h264.mp4  - H.264 baseline (libx264 preferred, libopenh264 fallback)
    fixtures/hevc.mp4  - H.265/HEVC (libx265 only; skipped if unavailable)
    fixtures/av1.mp4   - AV1 (libsvtav1; the codec from issue #11)

Source bg.mp4 is 128x72 @ 15fps for 2s, so we loop + upscale + reframerate
to get a long enough clip that per-frame work dominates over subprocess
startup and metadata parsing.

Some ffmpeg builds ship without libx264/libx265 (e.g. distro packages that
avoid GPL). This script picks the best available encoder per codec family
and skips a codec entirely if no software encoder is present. Hardware
encoders (vaapi/nvenc/qsv/amf) are intentionally not used: results would
depend on the host GPU.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
SOURCE = REPO_ROOT / "tests" / "e2e" / "fixtures" / "bg.mp4"
OUT_DIR = HERE / "fixtures"

# Default profile: 360p @ 30fps for 3s = 90 frames. Keeps the reverse
# scenario tractable (each backward jump reopens ffmpeg, ~250ms of startup).
# Use --big for the stress profile: 720p @ 30fps for 30s = 900 frames.
DEFAULT_PROFILE = {"width": 640, "height": 360, "fps": 30, "duration": 3}
BIG_PROFILE     = {"width": 1280, "height": 720, "fps": 30, "duration": 30}

# For each codec family, list encoders in preference order. First one available wins.
# Params are the ffmpeg flags to append after the encoder is chosen.
ENCODER_CHOICES = {
    "h264": [
        ("libx264",      ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "23", "-pix_fmt", "yuv420p"]),
        ("libopenh264",  ["-c:v", "libopenh264", "-b:v", "2M", "-pix_fmt", "yuv420p"]),
    ],
    "hevc": [
        ("libx265",      ["-c:v", "libx265", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p"]),
    ],
    "av1": [
        ("libsvtav1",    ["-c:v", "libsvtav1", "-preset", "8", "-crf", "35", "-pix_fmt", "yuv420p"]),
        ("libaom-av1",   ["-c:v", "libaom-av1", "-cpu-used", "8", "-crf", "35", "-pix_fmt", "yuv420p"]),
    ],
}


def _require(binary: str) -> None:
    if shutil.which(binary) is None:
        sys.exit(f"error: {binary} not found on PATH")


def _available_encoders() -> set[str]:
    """Return the set of encoder names this ffmpeg was built with."""
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True, text=True, check=True,
    ).stdout
    names: set[str] = set()
    for line in out.splitlines():
        parts = line.strip().split(None, 2)
        # Encoder rows look like: " V....D libopenh264   OpenH264 ..."
        if len(parts) >= 2 and parts[0].startswith("V"):
            names.add(parts[1])
    return names


def _pick_encoder(name: str, available: set[str]) -> tuple[str, list[str]] | None:
    for enc, flags in ENCODER_CHOICES[name]:
        if enc in available:
            return enc, flags
    return None


def _encode(name: str, enc: str, extra: list[str], profile: dict, force: bool) -> Path:
    out = OUT_DIR / f"{name}.mp4"
    if out.exists() and not force:
        print(f"  {out.name}: exists, skipping (use --force to regenerate)")
        return out

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-stream_loop", "-1",
        "-i", str(SOURCE),
        "-t", str(profile["duration"]),
        "-vf", f"scale={profile['width']}:{profile['height']}",
        "-r", str(profile["fps"]),
        "-an",
        *extra,
        str(out),
    ]
    print(f"  {out.name}: encoding with {enc}...")
    subprocess.run(cmd, check=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-encode even if the output exists")
    parser.add_argument("--big", action="store_true",
                        help="Use the stress profile (720p, 30s, 900 frames) instead of the default (360p, 3s, 90 frames)")
    args = parser.parse_args()

    _require("ffmpeg")

    if not SOURCE.exists():
        sys.exit(f"error: source video not found at {SOURCE}")

    profile = BIG_PROFILE if args.big else DEFAULT_PROFILE

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    available = _available_encoders()
    print(f"Generating fixtures in {OUT_DIR}")
    print(f"Source: {SOURCE} -> {profile['width']}x{profile['height']} @ {profile['fps']}fps for {profile['duration']}s")

    skipped: list[str] = []
    for name in ENCODER_CHOICES:
        pick = _pick_encoder(name, available)
        if pick is None:
            candidates = ", ".join(e for e, _ in ENCODER_CHOICES[name])
            print(f"  {name}.mp4: skipped (no software encoder found; tried {candidates})")
            skipped.append(name)
            continue
        _encode(name, pick[0], pick[1], profile, args.force)

    if skipped:
        print()
        print("note: skipped codecs won't be benchmarked. To include them, install")
        print("      an ffmpeg build that ships the missing encoders and re-run.")


if __name__ == "__main__":
    main()
