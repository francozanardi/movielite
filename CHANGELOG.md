# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-11-09

### Fixed

- Memory leak when rendering multiple video clips. Clips are now closed progressively as they finish rendering instead of keeping all clips open until the end.
- Zoom built-in effects position were improved, now the render process supports float values as position. It doesn't support subpixeling, but it rounds the floats, instead of just ignoring the decimal part.

## [0.1.0] - 2025-11-08

- Initial release.
