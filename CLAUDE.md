# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`movielite` is a Python video editing library packaged for PyPI. It is a lightweight, CPU-focused alternative to MoviePy that leans on Numba JIT for hot paths (alpha blending, transforms). Requires Python 3.10-3.13 and a system FFmpeg (`ffmpeg` + `ffprobe` on PATH — enforced at import time by [bootstrap.py](src/movielite/bootstrap.py)).

## Common commands

```bash
# Editable install with test extras
pip install -e ".[test]"

# Run the full test suite with coverage (mirrors CI)
pytest --cov=src/movielite --cov-branch --cov-report=xml

# Run a single test
pytest tests/test_basic_functionality.py::test_image_clip_creation

# Run the benchmark against moviepy 2.2.1 (requires an input video)
python benchmarks/compare_moviepy.py --input /path/to/input.mp4
```

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs `pytest` across Python 3.10-3.13 on Ubuntu with FFmpeg preinstalled. There is no linter or formatter configured.

## Architecture

### Class hierarchy

Everything that lives on the timeline derives from [`MediaClip`](src/movielite/core/media_clip.py) (holds `start`, `duration`, `speed`). Two branches:

- [`GraphicClip`](src/movielite/core/graphic_clip.py) — visual base. Adds position/opacity/scale/rotation/size (all stored internally as `Callable[[float], T]` so any property can be animated), a stack of pixel transforms and frame transforms, and an optional mask (another `GraphicClip`). Subclasses: `VideoClip`, `AlphaVideoClip`, `ImageClip`, `TextClip`, `CompositeClip`, `AlphaCompositeClip`.
- [`AudioClip`](src/movielite/audio/audio_clip.py) — audio base. Sample-level access, effects, volume curves.

Setters use `Self` return types for chaining. When you call `.set_position((x, y))` the tuple is wrapped into a `lambda t: (x, y)` — always treat these properties as functions of time internally.

### Rendering pipeline

[`VideoWriter`](src/movielite/core/video_writer.py) is the sink. It:

1. Sorts clips into `_graphic_clips` and `_audio_clips` (adding a `VideoClip`'s audio automatically).
2. Auto-derives `duration` (`max(clip.end)`) and `size` (first clip's size) if unset.
3. Per output frame: filters to active clips by `start`/`duration`, calls `active_clips[0].render_as_background(...)` for the base layer, then loops `clip.render(frame, t)` for the rest, and pipes bgr24 rawvideo into an `ffmpeg` subprocess encoding libx264 + yuv420p to MP4.
4. With `processes > 1`, splits the frame range across `multiprocess.Process` workers, writes N part files, concatenates, then muxes audio in a final pass.

Output is intentionally limited to MP4/libx264/AAC; there is no codec/container abstraction. Quality is picked via the [`VideoQuality`](src/movielite/enums.py) preset.

### Performance-sensitive bits

- Blending kernels live inline in `GraphicClip` and are decorated with `@numba.jit(nopython=True, cache=True)`. First run pays a JIT compile cost — don't be surprised by warm-up in benchmarks.
- [`core/empty_frame.py`](src/movielite/core/empty_frame.py) caches zero-filled numpy arrays keyed by `(dtype, components, width, height)` and reuses them across frames. Any code that writes into one of these buffers must call `mark_as_dirty()`; `clean_all()` is called between frames.
- `high_precision_blending=False` (the default on `VideoWriter.write`) keeps compositing in `uint8`. Only opt into float32 when many transparent layers are stacked — the README notes ~4× memory hit.

### Effects vs transitions

Effects and transitions are **mutation objects**, not wrappers — they modify a clip in place via `apply()`:

- [`vfx.GraphicEffect`](src/movielite/vfx/base.py): implements `apply(clip)`. Applied via `clip.add_effect(effect)`. Typical implementation appends a `frame_transform` (a `(frame, t) -> frame` function).
- [`afx`](src/movielite/afx/) — same pattern for audio.
- [`vtx.Transition`](src/movielite/vtx/base.py): implements `apply(clip1, clip2)`, called via `clip1.add_transition(clip2, transition)`. Base class provides `_validate_clips_are_consecutive` and `_validate_clips_have_overlap` helpers — reuse them when writing new transitions.

When adding a new effect, prefer chaining onto the existing transform stacks (`add_transform`, pixel transforms) rather than subclassing the clip. See [docs/advanced.md](docs/advanced.md) for a worked example.

### CompositeClip caveat

[`CompositeClip`](src/movielite/composite/composite_clip.py) exists so a group of clips can be transformed/masked as a unit, but it adds an intermediate composition layer. For plain "put multiple clips on the timeline," prefer `VideoWriter.add_clips(...)` — the class docstring documents this tradeoff and it is easy to reach for `CompositeClip` unnecessarily. Inside a `CompositeClip`, child `start` and position are **relative to the composite**, not absolute timeline coordinates.

### Public surface

The top-level [`movielite/__init__.py`](src/movielite/__init__.py) is the source of truth for what's exported. When adding a new clip type or public class, add it to `__all__` there.
