# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Playback speed control via `set_speed()` method for all clip types
- Rotation support via `set_rotation()` method and `vfx.Rotation` effect

### Fixed

- `AlphaVideoClip.subclip()` now correctly returns `AlphaVideoClip` instead of `VideoClip`, preserving transparency and loop behavior

## [0.2.1] - 2025-11-15

### Changed

- `CompositeClip` and `AlphaCompositeClip` constructor signature changed. Now requires explicit `start` parameter and optional `duration`. The `duration` parameter is optional and auto-calculated from child clips if not provided.

## [0.2.0] - 2025-11-15

### Added

- Support for composite clips with `CompositeClip` and `AlphaCompositeClip` classes for grouping multiple clips as a single unit
- `high_precision_blending` parameter in `VideoWriter.write()` to control blending precision (float32 vs uint8)
- `high_precision_blending` parameter in `CompositeClip` and `AlphaCompositeClip` for independent precision control

### Changed

- **Performance improvement**: Background frames now use uint8 by default during blending instead of float32, reducing memory usage and improving rendering speed
- float32 precision is now opt-in via `high_precision_blending=True`, recommended only for multiple layers with transparency or subtle gradients

### Fixed

- Clip ordering preservation during rendering - replaced set with list to maintain proper z-order for composition and blending
- Video clip subclipping now correctly copies pixel transforms to the new clip instance

## [0.1.1] - 2025-11-09

### Fixed

- Memory leak when rendering multiple video clips. Clips are now closed progressively as they finish rendering instead of keeping all clips open until the end.
- Zoom built-in effects position were improved, now the render process supports float values as position. It doesn't support subpixeling, but it rounds the floats, instead of just ignoring the decimal part.

## [0.1.0] - 2025-11-08

- Initial release.
