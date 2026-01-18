# MovieLite

A fast and intuitive Python video editing library, designed as a lightweight alternative to MoviePy.

<div align="center">
  <img src="https://res.cloudinary.com/dlvnbnb9v/image/upload/v1764024572/movielite_efcxcf.gif" alt="MovieLite Demo" width="800">
</div>

> The animation above was fully generated using **MovieLite** itself!  
> Check out the code [here](https://github.com/francozanardi/movielite/blob/main/docs/icon/movielite_gif.py).

## Overview

`MovieLite` is a Python video editing library built with a focus on **speed and simplicity for common workflows**. It offers a clean, chainable API that will feel familiar to MoviePy users, but delivers significant performance gains for CPU-based rendering.

The library achieves this speed by leveraging **Numba's JIT compilation** for critical operations like alpha blending and transformations. While it doesn't aim for feature-for-feature parity with MoviePy and currently lacks GPU acceleration, it excels at providing a much faster experience for everyday tasks, such as:

- Applying transformations (zoom, position, scale).
- Compositing overlays (text, images, other videos).
- Rendering projects with multiple effects.

If you love MoviePy's approach but need a significant speed boost for your CPU-bound projects, `MovieLite` is for you.

## Key Features

- **Frame-by-frame processing**: Full control over every frame and audio sample
- **Performance optimized**: Uses Numba JIT compilation for critical rendering operations
- **Clean API**: Chainable methods for intuitive video editing workflows
- **Comprehensive effects library**: Built-in visual effects (vfx), audio effects (afx), and transitions (vtx)
- **Multiprocessing support**: Parallel rendering for faster video generation
- **Audio mixing**: Mix multiple audio tracks with per-sample control
- **Memory efficient**: Streaming architecture for large video files

## Performance Comparison

`MovieLite` is designed to be faster than moviepy for common video editing tasks. Performance improvements come from:

1. **Numba JIT compilation**: Critical rendering loops are compiled to native code
2. **Optimized compositing**: Efficient alpha blending and frame composition
3. **Memory management**: Streaming architecture reduces memory footprint
4. **Multiprocessing**: Parallel frame rendering for multi-core systems

### Benchmark Results

To run benchmarks comparing movielite with moviepy 2.2.1:

```bash
python benchmarks/compare_moviepy.py --input /path/to/input
```

Real benchmark results (1280x720 video, 30fps):

| Task | movielite | moviepy | Speedup |
|------|-----------|---------|---------|
| No processing | 6.34s | 6.71s | **1.06x** 🚀 |
| Video zoom | 9.52s | 31.81s | **3.34x** 🚀 |
| Fade in/out | 8.53s | 9.03s | **1.06x** 🚀 |
| Text overlay | 7.82s | 35.35s | **4.52x** 🚀 |
| Video overlay | 18.22s | 75.47s | **3.14x** 🚀 |
| Alpha video overlay | 10.75s | 42.11s | **3.92x** 🚀 |
| Complex mix* | 38.07s | 175.31s | **4.61x** 🚀 |
| **Total** | **99.24s** | **375.79s** | **3.79x** 🚀 |

*Complex mix includes: video with zoom + fade, image clips with fade, text overlay, video overlay - all composed together.

**movielite excels at:**
- Transform operations (zoom, scale, resize) - **up to 3.17x faster**
- Text overlays and compositing - **up to 3.75x faster**
- Video overlays and layering - **up to 3.83x faster**
- Alpha channel compositing - **up to 3.36x faster**
- Complex multi-effect compositions - **up to 4.21x faster**

*Results may vary based on hardware, video codec, and complexity.*

## Architecture

### Frame-by-Frame Processing

Like moviepy, movielite operates on a frame-by-frame basis:

```python
# Every frame is individually processed
for frame_idx in range(total_frames):
    t = frame_idx / fps
    frame = clip.get_frame(t)  # Get raw frame
    frame = apply_transforms(frame, t)  # Apply effects
    frame = blend_with_other_clips(frame, t)  # Composite
    write_frame_to_output(frame)
```

This approach provides:
- Complete control over every pixel
- Ability to apply time-based effects
- Support for complex compositing operations
- Memory efficiency through streaming

### Numba Optimization

Critical operations are JIT-compiled with Numba:

```python
@numba.jit(nopython=True, cache=True)
def blend_foreground_with_bgr_background_inplace(
    background, foreground, x, y, opacity, mask, ...
):
    # Pixel-perfect alpha blending at native speed
    ...
```

This provides near-native performance for:
- Alpha blending operations
- Pixel-wise transformations
- Color space conversions

## What It Supports

### Video Capabilities
- Video clips with frame-level access
- Alpha video clips (transparency support via AlphaVideoClip)
- Image clips (static images as video frames)
- Text rendering (via pictex library)
- Mask support for advanced compositing effects
- Video effects: fade, blur, color adjustments, vignette, zoom, glitch effects, rotation
- Video transitions: crossfade, dissolve, blur dissolve
- Position, scale, opacity, rotation, and size transformations
- Custom frame transformations
- Video looping
- Playback speed control

### Audio Capabilities
- Audio clips with sample-level access
- Audio effects: fade in/out
- Volume control and volume curves
- Multiple audio track mixing
- Audio from video files
- Custom audio transformations

### Output Formats
- **Video codec**: libx264 (H.264)
- **Container format**: MP4
- **Audio codec**: AAC
- **Quality presets**: LOW, MIDDLE, HIGH, VERY_HIGH

## Limitations

- Output is limited to MP4 format with libx264 codec
- No GPU acceleration (CPU-based rendering only)

## Installation

```bash
pip install movielite
```

## Requirements

- Python 3.10+
- FFmpeg (must be installed and available in PATH)
- NumPy
- OpenCV (opencv-python)
- Numba (for JIT compilation)
- multiprocess
- tqdm
- pictex (for TextClip)

### Installing FFmpeg

**Windows:**
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to a permanent location (e.g., `C:\ffmpeg`)
3. Add the `bin` directory to your PATH environment variable

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt-get install ffmpeg  # Debian/Ubuntu
sudo yum install ffmpeg      # CentOS/RHEL
```

## Quick Start

### Basic Video Editing

```python
from movielite import VideoClip, VideoWriter

# Load and extract a segment
clip = VideoClip("input.mp4")
subclip = clip.subclip(10, 15)  # Extract seconds 10-15

# Create output
writer = VideoWriter("output.mp4", fps=30)
writer.add_clip(
    subclip
    .set_position((100, 100))
    .set_opacity(0.8)
)
writer.write()

clip.close()
```

### Adding Effects

```python
from movielite import VideoClip, VideoWriter, vfx

clip = VideoClip("video.mp4")

# Chain multiple effects
clip.add_effect(vfx.FadeIn(1.0))
clip.add_effect(vfx.FadeOut(1.5))
clip.add_effect(vfx.Blur(intensity=3.0))

writer = VideoWriter("output.mp4", fps=clip.fps, size=clip.size)
writer.add_clip(clip)
writer.write()

clip.close()
```

### Text Overlays

```python
from movielite import VideoClip, TextClip, VideoWriter
from pictex import Canvas, LinearGradient, Shadow

# Create styled text
canvas = (
    Canvas()
    .font_family("Arial")
    .font_size(60)
    .color("white")
    .padding(20)
    .background_color(LinearGradient(["#2C3E50", "#FD746C"]))
    .border_radius(10)
    .text_shadows(Shadow(offset=(2, 2), blur_radius=3, color="black"))
)

video = VideoClip("background.mp4")
text = TextClip("Hello World", start=2, duration=3, canvas=canvas)
text.set_position((video.size[0] // 2 - text.size[0] // 2, 100))

writer = VideoWriter("output.mp4", fps=video.fps, size=video.size)
writer.add_clip(video)
writer.add_clip(text)
writer.write()

video.close()
```

### Concatenating Videos

```python
from movielite import VideoClip, VideoWriter

clip1 = VideoClip("intro.mp4", start=0)
clip2 = VideoClip("main.mp4", start=clip1.end)
clip3 = VideoClip("outro.mp4", start=clip2.end)

writer = VideoWriter("final.mp4", fps=30)
writer.add_clips([clip1, clip2, clip3])
writer.write()

clip1.close()
clip2.close()
clip3.close()
```

### Audio Mixing

```python
from movielite import VideoClip, AudioClip, VideoWriter, afx

video = VideoClip("video.mp4")

# Background music at 50% volume
music = AudioClip("background.mp3", start=0, volume=0.5)
music.add_effect(afx.FadeIn(2)).add_effect(afx.FadeOut(2))

# Sound effect at specific time
sfx = AudioClip("ding.wav", start=5.0, volume=1.0)

writer = VideoWriter("output.mp4", fps=video.fps)
writer.add_clip(video)  # Video includes its own audio track
writer.add_clip(music)
writer.add_clip(sfx)
writer.write()

video.close()
```

### Transitions

```python
from movielite import VideoClip, VideoWriter, vtx

clip1 = VideoClip("scene1.mp4", start=0, duration=5)
clip2 = VideoClip("scene2.mp4", start=4, duration=5)  # 1s overlap

# Apply crossfade transition
clip1.add_transition(clip2, vtx.CrossFade(duration=1))

writer = VideoWriter("output.mp4", fps=30)
writer.add_clips([clip1, clip2])
writer.write()

clip1.close()
clip2.close()
```

### Speed Control

```python
from movielite import VideoClip, VideoWriter

# Create a slow-motion effect
video = VideoClip("action.mp4", start=0, duration=5)
video.set_speed(0.5)  # 5s of source plays in 10s (half speed)

writer = VideoWriter("slow_motion.mp4", fps=video.fps)
writer.add_clip(video)
writer.write()

video.close()
```

### Custom Frame Transformations

```python
import cv2
import numpy as np
from movielite import VideoClip, VideoWriter

clip = VideoClip("video.mp4")

# Apply custom sepia effect
def sepia_transform(frame: np.ndarray, t: float) -> np.ndarray:
    kernel = np.array([
        [0.131, 0.534, 0.272],
        [0.168, 0.686, 0.349],
        [0.189, 0.769, 0.393]
    ])
    sepia = cv2.transform(frame, kernel)
    return np.clip(sepia, 0, 255).astype(np.uint8)

clip.add_transform(sepia_transform)

writer = VideoWriter("output.mp4", fps=clip.fps)
writer.add_clip(clip)
writer.write()

clip.close()
```

### Masking for Advanced Compositing

```python
import numpy as np
from movielite import VideoClip, TextClip, VideoWriter
from pictex import Canvas

# Video to be masked
video = VideoClip("waves.mp4", start=0, duration=10)

# Create text as mask
canvas = Canvas().font_size(200).color("white").background_color("transparent")
text = TextClip("Hello World!", start=0, duration=10, canvas=canvas)

# Animate mask position and scale
text.set_position(lambda t: (
    960 - text.size[0] // 2,
    500 + int(20 * np.sin(2 * np.pi * (t / text.duration)))
))
text.set_scale(lambda t: 1.0 + 0.4 * (t / text.duration))

# Apply mask - video only visible through text
video.set_mask(text)
video.set_size(1920, 1080)

writer = VideoWriter("output.mp4", fps=30, size=(1920, 1080))
writer.add_clip(video)
writer.write()

video.close()
```

### Multiprocessing for Faster Rendering

```python
from movielite import VideoClip, VideoWriter, VideoQuality

clip = VideoClip("input.mp4")

writer = VideoWriter("output.mp4", fps=clip.fps, size=clip.size)
writer.add_clip(clip)

# Use 8 parallel processes for rendering
writer.write(processes=8, video_quality=VideoQuality.HIGH)

clip.close()
```

## API Reference

For detailed API documentation, see [docs/api.md](https://github.com/francozanardi/movielite/blob/main/docs/api.md).

### Core Classes

- [VideoClip](https://github.com/francozanardi/movielite/blob/main/docs/api.md#videoclip) - Load and manipulate video files
- [AlphaVideoClip](https://github.com/francozanardi/movielite/blob/main/docs/api.md#alphavideoclip) - Video with alpha channel support
- [ImageClip](https://github.com/francozanardi/movielite/blob/main/docs/api.md#imageclip) - Static images as video frames
- [TextClip](https://github.com/francozanardi/movielite/blob/main/docs/api.md#textclip) - Rendered text overlays
- [AudioClip](https://github.com/francozanardi/movielite/blob/main/docs/api.md#audioclip) - Audio track handling
- [VideoWriter](https://github.com/francozanardi/movielite/blob/main/docs/api.md#videowriter) - Render composition to file

### Effect Modules

- [vfx](https://github.com/francozanardi/movielite/blob/main/docs/api.md#vfx) - Visual effects (fade, blur, color, zoom, glitch)
- [afx](https://github.com/francozanardi/movielite/blob/main/docs/api.md#afx) - Audio effects (fade in/out)
- [vtx](https://github.com/francozanardi/movielite/blob/main/docs/api.md#vtx) - Video transitions (crossfade, dissolve)

## Advanced Usage

For advanced topics, see [docs/advanced.md](https://github.com/francozanardi/movielite/blob/main/docs/advanced.md):

- Custom effect development
- Performance optimization techniques
- Memory management strategies
- Advanced audio processing
- Masking and compositing techniques
- Integration with other libraries

## Examples

Additional examples are available in the [examples/](https://github.com/francozanardi/movielite/blob/main/examples/) directory:

- [basic_editing.py](https://github.com/francozanardi/movielite/blob/main/examples/basic_editing.py) - Simple cuts and concatenation
- [effects_showcase.py](https://github.com/francozanardi/movielite/blob/main/examples/effects_showcase.py) - All built-in effects
- [text_animations.py](https://github.com/francozanardi/movielite/blob/main/examples/text_animations.py) - Animated text overlays
- [audio_mixing.py](https://github.com/francozanardi/movielite/blob/main/examples/audio_mixing.py) - Complex audio compositions
- [transitions.py](https://github.com/francozanardi/movielite/blob/main/examples/transitions.py) - Transition examples
- [masking_effects.py](https://github.com/francozanardi/movielite/blob/main/examples/masking_effects.py) - Advanced masking techniques

## Roadmap and Future Directions

Our focus will be on three key areas: performance, developer experience, and flexibility.

Contributions are highly welcome! If any of these ideas resonate with you, feel free to open an issue or a pull request to discuss it.

### 1. Performance Enhancements

- **GPU Acceleration:** While MovieLite is well optimized for CPU, adding optional GPU support (e.g., using CuPy or PyTorch for transformations and blending) is a major goal. This would unlock another order-of-magnitude performance boost for users with compatible hardware.
- **Core Rendering Optimizations:** We plan to introduce more intelligent caching. For instance, an `ImageClip` with a static scale shouldn't be re-rendered on every frame.
- **Expanded Numba JIT Usage:** Some of the current visual effects (`vfx`) can be rewritten using Numba to run at near-native speed, further improving rendering times for complex compositions.

### 2. Developer Experience (DevEx)

- **A More Intuitive API:** We want to make the library even more pleasant to work with. This includes:
    - Adding convenience features like string-based positioning (`.set_position("center")`).
    - Implementing a deep `.copy()` method for clips to make duplication easier.
    - Providing ways to manage the effect stack, such as removing or replacing transformations after they've been added.
- **Better Type Hinting and Documentation:** Improving inline documentation and type hints to enhance autocompletion and code analysis in modern editors.

### 3. Flexibility and Advanced Control

- **Flexible Output Options:** We aim to give users more control over the final render by:
    - Officially supporting more video/audio codecs and container formats (e.g., WebM, MOV).
    - Exposing FFmpeg parameters directly in the `VideoWriter`, similar to MoviePy's `ffmpeg_params`, for advanced users who need fine-grained control over encoding quality, presets, and other options.
- **Expanded Effects Library:** Continuously adding new, performant effects to the `vfx`, `afx`, and `vtx` modules based on community feedback and common use cases.

## License

MIT License - see [LICENSE](https://github.com/francozanardi/movielite/blob/main/LICENSE) for details.

## Changelog

See [CHANGELOG.md](https://github.com/francozanardi/movielite/blob/main/CHANGELOG.md) for version history and changes.
