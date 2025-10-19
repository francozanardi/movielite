# movielite

A performance-oriented Python video editing library focused on speed and simplicity.

## Overview

`movielite` is a lightweight alternative to moviepy, designed for faster video processing with a clean, chainable API. It provides essential video editing capabilities with emphasis on performance.

## Features

- 🎬 **Video Clips**: Load and manipulate video files
- 🖼️ **Image Clips**: Use images as video clips
- 📝 **Text Clips**: Render styled text using [pictex](https://github.com/yourusername/pictex)
- 🎵 **Audio Support**: Overlay multiple audio tracks
- 🔗 **Concatenation**: Join multiple clips seamlessly
- ✂️ **Subclipping**: Extract segments from clips
- 🎨 **Effects**: Built-in fade in/out, opacity, scale, position
- 🔧 **Custom Transformations**: Apply custom frame transformations
- 🚀 **Multiprocessing**: Render videos using multiple CPU cores

## Installation

```bash
pip install movielite
```

For text rendering support:
```bash
pip install pictex
```

## Quick Start

### Basic Video Editing

```python
from movielite import VideoClip, VideoWriter

# Load a video clip and extract a segment
clip = VideoClip("input.mp4")
subclip = clip.subclip(10, 15)

# Create a writer and render
writer = VideoWriter("output.mp4", fps=30, size=(1920, 1080))
writer.add_clip(subclip.set_position((100, 100)))
writer.write()
```

### Adding Text Overlays

```python
from movielite import VideoClip, TextClip, VideoWriter
from pictex import Canvas, LinearGradient, Shadow

# Create styled text
canvas = (
    Canvas()
    .font_family("Poppins-Bold.ttf")
    .font_size(60)
    .color("white")
    .padding(20)
    .background_color(LinearGradient(["#2C3E50", "#FD746C"]))
    .border_radius(10)
    .text_shadows(Shadow(offset=(2, 2), blur_radius=3, color="black"))
)

text = TextClip("Hello World! 🎨", start=2, duration=3, canvas=canvas)
text.set_position((640, 360))

# Overlay text on video
bg_video = VideoClip("video.mp4")
writer = VideoWriter("output.mp4", fps=bg_video.fps, size=bg_video.size)
writer.add_clip(bg_video)  # Background video
writer.add_clip(text)       # Text overlay
writer.write()
```

### Concatenating Videos

```python
from movielite import VideoClip, concatenate_videoclips

clip1 = VideoClip("intro.mp4")
clip2 = VideoClip("main.mp4")
clip3 = VideoClip("outro.mp4")

final = concatenate_videoclips([clip1, clip2, clip3])
# final is a CompositeClip that can be rendered
```

### Adding Audio

```python
from movielite import VideoClip, VideoWriter, AudioClip

# Load video
bg_video = VideoClip("video.mp4")

# Create writer
writer = VideoWriter("output.mp4", fps=bg_video.fps, size=bg_video.size)
writer.add_clip(bg_video)

# Add background music
music = AudioClip("background_music.mp3", start=0, volume=0.5)
writer.add_audio(music)

# Add sound effect at 5 seconds
sfx = AudioClip("ding.wav", start=5, volume=1.0)
writer.add_audio(sfx)

writer.write()
```

### Using Effects

```python
from movielite import VideoClip
from movielite.fx import fade_in, fade_out, resize

clip = VideoClip("video.mp4")

# Chain effects
clip = fade_in(clip, duration=1.0)
clip = fade_out(clip, duration=1.0)
clip = resize(clip, width=1280)

# Or use methods
clip.set_opacity(0.8)
clip.set_scale(0.5)
```

### Custom Frame Transformations

```python
import cv2
from movielite import VideoClip

clip = VideoClip("video.mp4")

# Apply custom transformation to each frame
def make_grayscale(frame, t):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

clip.transform_frame(make_grayscale)
```

### Creating Image Clips

```python
from movielite import ImageClip

# From file
img_clip = ImageClip("photo.jpg", start=0, duration=5)

# From solid color
color_clip = ImageClip.from_color(
    color=(255, 0, 0),  # Red
    size=(1920, 1080),
    duration=3
)
```

### Working with CompositeClips

```python
from movielite import CompositeClip, VideoClip, ImageClip, TextClip

# Create multiple clips
video = VideoClip("background.mp4", start=0, duration=10)
logo = ImageClip("logo.png", start=0, duration=10).set_position((50, 50))
title = TextClip("My Video", start=1, duration=3).set_position((640, 100))

# Combine them
composite = CompositeClip(
    clips=[video, logo, title],
    size=(1920, 1080)
)
```

## API Reference

### Core Classes

#### `VideoClip`
Load and manipulate video files.
- `VideoClip(path, start=0, duration=None, offset=0)`
- Methods: `subclip(start, end)`, `set_position()`, `set_opacity()`, `set_scale()`, `set_size()`, `transform_frame()`

#### `ImageClip`
Display static images as video clips.
- `ImageClip(source, start=0, duration=5.0)`
- `ImageClip.from_color(color, size, start=0, duration=5.0)`

#### `TextClip`
Render styled text using pictex.
- `TextClip(text, start=0, duration=5.0, canvas=None)`

#### `AudioClip`
Handle audio tracks.
- `AudioClip(path, start=0, duration=None, volume=1.0, offset=0)`
- Methods: `subclip(start, end)`, `set_volume(volume)`

#### `CompositeClip`
Combine multiple clips.
- `CompositeClip(clips, start=0, duration=None, size=(1920, 1080))`
- Methods: `add_clip(clip)`

#### `VideoWriter`
Write clips to a video file.
- `VideoWriter(output_path, fps=30, size=(1920, 1080), duration=None)`
- Methods: `add_clip(clip)`, `add_audio(audio)`, `write()`

### Utility Functions

#### `concatenate_videoclips(clips)`
Join video clips sequentially.

#### `concatenate_audioclips(clips)`
Join audio clips sequentially.

### Effects (movielite.fx)

#### Video Effects
- `fade_in(clip, duration=1.0)`
- `fade_out(clip, duration=1.0)`
- `resize(clip, width=None, height=None)`

#### Audio Effects
- `volumex(clip, factor)`

## Performance Tips

1. **Use multiprocessing**: Enable `use_multiprocessing=True` in `render()` for faster rendering
2. **Set appropriate quality**: Use `VideoQuality.LOW` for faster encoding during development
3. **Optimize clip duration**: Only load the portion of video you need using `offset` and `duration`
4. **Resize early**: If you need smaller output, resize clips before rendering

```python
from movielite import VideoWriter, VideoQuality

writer = VideoWriter("output.mp4", fps=30, size=(1920, 1080))
# ... add clips ...
writer.write(
    use_multiprocessing=True,
    processes=8,
    video_quality=VideoQuality.HIGH
)
```

## Requirements

- Python 3.10+
- OpenCV (opencv-python)
- NumPy
- FFmpeg (must be installed and in PATH)
- pydub
- multiprocess
- tqdm
- pictex (optional, for TextClip)

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

This library was extracted and refactored from the [pycaps](https://github.com/yourusername/pycaps) project, focusing on the video rendering capabilities as a standalone library.
