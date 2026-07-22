# Bundled FFmpeg Binaries

## Motivation

`movielite` currently requires the user to install FFmpeg (`ffmpeg` and
`ffprobe`) on the system and have both binaries available on `PATH`. This is
enforced at import time by [bootstrap.py](../src/movielite/bootstrap.py). The
requirement adds a non-trivial onboarding step, particularly for Windows and
macOS users, and for reproducible environments (Docker images, CI runners)
where the FFmpeg install has to be scripted separately.

The goal of this initiative is to offer a first-class, opt-in path that
delivers pre-built FFmpeg binaries alongside the library, without forcing
duplication on users who already have FFmpeg installed system-wide.

## Approach

Distribute the binaries through a **separate companion package** exposed as an
optional extra of the main package. The main `movielite` distribution stays a
thin, pure-Python wheel with no binary payload; users who want the bundled
binaries opt in explicitly:

```
pip install movielite            # unchanged behaviour, relies on system FFmpeg
pip install movielite[ffmpeg]    # additionally installs the companion package
```

The companion package (working name: `movielite-ffmpeg-bin`) ships one wheel
per supported platform, each containing the FFmpeg and FFprobe executables for
that platform. The `[ffmpeg]` extra on `movielite` declares a dependency on
this companion package.

This model mirrors the well-established `imageio` + `imageio-ffmpeg` split and
has the following properties:

- Users with a system FFmpeg install pay no additional cost.
- Users without a system FFmpeg install resolve the dependency in a single
  `pip` command, with no shell-level installation step.
- All platform-specific wheel-building complexity is isolated in the companion
  package's release pipeline and does not affect the main package's release
  workflow.

### Resolution order at runtime

`bootstrap.py` must be updated to locate the executables in the following
order:

1. The companion package, if installed. Its wheels expose the binaries at a
   known path inside the installed distribution.
2. The `PATH` environment variable (current behaviour).

This ordering ensures that when the user has explicitly opted in to the
bundled binaries, those are the ones used, avoiding surprises caused by an
unrelated system FFmpeg that may differ in version or codec support. If the
companion package is absent, existing behaviour is preserved verbatim.

## Binary sources

### Linux (glibc) and Windows

Use the **GPL** builds published by
[BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds), which is the
community-standard source for static FFmpeg builds (11k+ stars, MIT-licensed
build scripts, builds produced by public GitHub Actions and therefore
auditable).

The **`-gpl-`** variant is required. The `-lgpl-` variant omits `libx264` and
`libx265`, both of which are GPL-licensed and both of which are needed by
`movielite` — the writer encodes with libx264 by default (see
[video_writer.py](../src/movielite/core/video_writer.py)).

Target assets from each BtbN release:

- `ffmpeg-nX.Y-latest-linux64-gpl-X.Y.tar.xz` (x86_64)
- `ffmpeg-nX.Y-latest-linuxarm64-gpl-X.Y.tar.xz` (aarch64)
- `ffmpeg-nX.Y-latest-win64-gpl-X.Y.zip` (Windows x86_64)

Each download must be checksum-verified against the release metadata before
being packaged into a wheel.

### macOS

BtbN does not build for macOS. Use:

- [evermeet.cx/ffmpeg](https://evermeet.cx/ffmpeg/) for macOS x86_64
- [osxexperts.net](https://www.osxexperts.net/) for macOS arm64 (Apple
  Silicon)

Both sources are long-standing community references and provide static builds
of both `ffmpeg` and `ffprobe`. Codec inclusion (in particular `libx264`) must
be verified at implementation time; historically these builds are "full" and
include the same GPL codec set as the BtbN GPL variant.

If maintaining two macOS sources becomes a burden, a second-phase alternative
is to build FFmpeg from source in a `macos-13` (x86_64) and `macos-latest`
(arm64) runner as part of the release workflow. This trades ~40 minutes of
CI time per architecture for full control over the build.

## Wheel matrix

The companion package publishes the following wheels for each release:

| Platform tag              | Architecture | Binary source        |
|---------------------------|--------------|----------------------|
| `manylinux_2_17_x86_64`   | x86_64       | BtbN (linux64 gpl)   |
| `manylinux_2_17_aarch64`  | aarch64      | BtbN (linuxarm64 gpl)|
| `macosx_10_15_x86_64`     | x86_64       | evermeet.cx          |
| `macosx_11_0_arm64`       | arm64        | osxexperts.net       |
| `win_amd64`               | x86_64       | BtbN (win64 gpl)     |

An `sdist` is also published to allow users on unsupported platforms to at
least see a meaningful failure message rather than a `pip` resolution error.

### Alpine / musl — deferred

BtbN does not publish `musl`-linked builds, and no equally reputable community
source is currently known. As a result, no `musllinux_*` wheel is published in
the first iteration. Alpine users install `movielite` without the extra and
provide FFmpeg through `apk add ffmpeg`, which matches the pre-initiative
behaviour and therefore introduces no regression.

Adding `musllinux_1_2_x86_64` support in a later iteration is straightforward
once we are willing to build FFmpeg from source inside an `alpine:latest`
container in the release workflow.

## Release pipeline changes

The current release workflow ([release.yml](../.github/workflows/release.yml))
targets a single pure-Python wheel and can remain unchanged.

The companion package requires its own release workflow, structured as a
`cibuildwheel` matrix (or an equivalent per-platform GitHub Actions matrix)
with the following steps per platform:

1. Download the platform-appropriate FFmpeg archive from the corresponding
   upstream (BtbN, evermeet, osxexperts).
2. Verify the archive against a known checksum.
3. Extract `ffmpeg` and `ffprobe` and stage them under a known path inside the
   package (for example `movielite_ffmpeg_bin/_bin/`).
4. Build the platform-specific wheel with the correct platform tag.
5. Publish all wheels + sdist to PyPI via Trusted Publishing, following the
   same OIDC-based flow already used by the main package.

## Licensing considerations

`libx264` and `libx265` are GPL-licensed. Distributing a build of FFmpeg that
includes them makes that build a GPL work.

Consequences:

- The **companion package must be licensed GPL** and must ship (or link to)
  the corresponding source of the FFmpeg build, which BtbN's release page
  already provides for its own builds.
- The **main `movielite` package is not affected**. `movielite` invokes FFmpeg
  as an external subprocess and does not link against it in any form. Under
  the accepted interpretation of the GPL, `movielite` can retain its current
  license. The user who installs `movielite[ffmpeg]` is the party assembling
  the GPL aggregate on their machine; the two packages remain independently
  licensed on PyPI.

Both points should be reflected in the companion package's `README`, its
`LICENSE` file, and in a short note added to the main `movielite` README next
to the installation instructions.

## Out of scope for this task

- Building custom FFmpeg with additional codecs or hardware acceleration
  support.
- Providing `musllinux` wheels (see Alpine section above).
- Replacing the subprocess-based FFmpeg invocation with a linked/embedded
  approach.
- Any change to the codec set or default encoding parameters used by
  `VideoWriter`.
