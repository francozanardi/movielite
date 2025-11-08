# API Reference

Complete API reference for movielite library.

## Table of Contents

- [Core Classes](#core-classes)
  - [MediaClip](#mediaclip)
  - [GraphicClip](#graphicclip)
  - [VideoClip](#videoclip)
  - [AlphaVideoClip](#alphavideoclip)
  - [ImageClip](#imageclip)
  - [TextClip](#textclip)
  - [AudioClip](#audioclip)
  - [VideoWriter](#videowriter)
- [Visual Effects (vfx)](#visual-effects-vfx)
  - [Fade Effects](#fade-effects)
  - [Blur Effects](#blur-effects)
  - [Color Effects](#color-effects)
  - [Zoom Effects](#zoom-effects)
  - [Glitch Effects](#glitch-effects)
  - [Other Effects](#other-effects)
- [Audio Effects (afx)](#audio-effects-afx)
- [Transitions (vtx)](#transitions-vtx)
- [Enumerations](#enumerations)
- [Utilities](#utilities)

---

## Core Classes

### MediaClip

Base class for all media clips (visual and audio).

**Constructor:**
```python
MediaClip(start: float, duration: float)
```

**Parameters:**
- `start` (float): Start time in the composition (seconds)
- `duration` (float): Duration of the clip (seconds)

**Properties:**
- `start` (float): Start time in seconds
- `duration` (float): Duration in seconds
- `end` (float): End time in seconds (start + duration)

**Methods:**

#### set_start(start: float) -> Self
Set the start time of this clip in the composition.

**Parameters:**
- `start` (float): Start time in seconds (must be >= 0)

**Returns:** Self for chaining

**Raises:** ValueError if start is negative

---

#### set_duration(duration: float) -> Self
Set the duration of this clip.

**Parameters:**
- `duration` (float): Duration in seconds (must be > 0)

**Returns:** Self for chaining

**Raises:** ValueError if duration is not positive

---

#### set_end(end: float) -> Self
Set the end time of this clip in the composition. Adjusts duration to match.

**Parameters:**
- `end` (float): End time in seconds (must be > start)

**Returns:** Self for chaining

**Raises:** ValueError if end is not greater than start

---

### GraphicClip

Base class for all visual/graphic clips (video, image, text).

Inherits from [MediaClip](#mediaclip).

**Constructor:**
```python
GraphicClip(start: float, duration: float)
```

**Properties:**
- `position` (Callable[[float], Tuple[int, int]]): Position function
- `opacity` (Callable[[float], float]): Opacity function
- `scale` (Callable[[float], float]): Scale function
- `size` (Tuple[int, int]): Size of the clip (width, height)
- `has_any_transform` (bool): Whether any transformations are applied

**Methods:**

#### set_position(value: Union[Callable[[float], Tuple[int, int]], Tuple[int, int]]) -> Self
Set the position of the clip.

**Parameters:**
- `value`: Either a tuple (x, y) or a function that takes time and returns (x, y)

**Returns:** Self for chaining

**Example:**
```python
# Static position
clip.set_position((100, 100))

# Animated position
clip.set_position(lambda t: (int(100 + t * 50), 100))
```

---

#### set_opacity(value: Union[Callable[[float], float], float]) -> Self
Set the opacity of the clip.

**Parameters:**
- `value`: Either a float (0-1) or a function that takes time and returns opacity

**Returns:** Self for chaining

**Example:**
```python
# Static opacity
clip.set_opacity(0.5)

# Animated opacity
clip.set_opacity(lambda t: min(1.0, t / 2.0))
```

---

#### set_scale(value: Union[Callable[[float], float], float]) -> Self
Set the scale of the clip.

**Parameters:**
- `value`: Either a float or a function that takes time and returns scale

**Returns:** Self for chaining

**Example:**
```python
# Static scale
clip.set_scale(0.5)

# Animated scale
clip.set_scale(lambda t: 1.0 + t * 0.1)
```

---

#### set_size(width: Optional[int] = None, height: Optional[int] = None) -> Self
Set the size of the clip, maintaining aspect ratio if only one dimension is provided.

**Parameters:**
- `width` (Optional[int]): Target width
- `height` (Optional[int]): Target height

**Returns:** Self for chaining

**Raises:** ValueError if both width and height are None or invalid

**Example:**
```python
# Explicit size
clip.set_size(width=1280, height=720)

# Maintain aspect ratio (width only)
clip.set_size(width=1280)

# Maintain aspect ratio (height only)
clip.set_size(height=720)
```

---

#### set_mask(mask: GraphicClip) -> Self
Set a mask for this clip. The mask determines which pixels are visible.

The mask is converted to grayscale, where white (255) means fully visible and black (0) means fully transparent. Gray values create partial transparency.

**Parameters:**
- `mask` (GraphicClip): A GraphicClip to use as mask

**Returns:** Self for chaining

**Examples:**

Simple image mask:
```python
image = ImageClip("photo.png")
mask = ImageClip("mask.png")
image.set_mask(mask)
```

Animated text mask:
```python
import numpy as np
from movielite import VideoClip, TextClip
from pictex import Canvas

# Video to be masked
video = VideoClip("waves.mp4", start=0, duration=10)

# Create animated text mask
canvas = Canvas().font_size(200).color("white").background_color("transparent")
text = TextClip("Hello World!", start=0, duration=10, canvas=canvas)

# Animate the mask
text.set_position(lambda t: (
    960 - text.size[0] // 2,
    500 + int(20 * np.sin(2 * np.pi * (t / text.duration)))
))
text.set_scale(lambda t: 1.0 + 0.4 * (t / text.duration))

# Apply mask - video only visible through text shape
video.set_mask(text)
```

---

#### add_transform(callback: Callable[[np.ndarray, float], np.ndarray]) -> Self
Apply a custom transformation to each frame at render time.

**Parameters:**
- `callback` (Callable): Function that takes (frame, time) and returns transformed frame

**Returns:** Self for chaining

**Note:** The frame must be in BGR or BGRA format and uint8 type.

**Example:**
```python
def make_grayscale(frame, t):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

clip.add_transform(make_grayscale)
```

---

#### add_effect(effect: GraphicEffect) -> Self
Apply a visual effect to this clip.

**Parameters:**
- `effect` (GraphicEffect): A GraphicEffect instance to apply

**Returns:** Self for chaining

**Example:**
```python
from movielite import vfx
clip.add_effect(vfx.FadeIn(2.0)).add_effect(vfx.FadeOut(1.5))
```

---

#### add_transition(next_clip: GraphicClip, transition: Transition) -> Self
Apply a transition effect between this clip and another clip.

**Parameters:**
- `next_clip` (GraphicClip): The clip to transition to
- `transition` (Transition): A Transition instance to apply

**Returns:** Self for chaining

**Example:**
```python
from movielite import vtx
clip1.add_transition(clip2, vtx.CrossFade(0.5))
```

---

#### get_frame(t_rel: float) -> np.ndarray
Get the frame at a relative time within the clip (abstract method).

**Parameters:**
- `t_rel` (float): Relative time within the clip (0 to duration)

**Returns:** Frame as numpy array (BGR or BGRA, uint8)

---

#### render(bg: np.ndarray, t_global: float) -> np.ndarray
Render this clip onto a background at a given global time.

**Parameters:**
- `bg` (np.ndarray): Background frame (BGR or BGRA format, float32 type)
- `t_global` (float): Global time in seconds

**Returns:** Background with this clip rendered on top

**Note:** Modifies the background in-place.

---

#### close()
Closes the graphic clip and releases any resources.

---

### VideoClip

A video clip that loads and processes frames in BGR format (no alpha channel).

Inherits from [GraphicClip](#graphicclip).

**Constructor:**
```python
VideoClip(
    path: str,
    start: float = 0,
    duration: Optional[float] = None,
    offset: float = 0
)
```

**Parameters:**
- `path` (str): Path to the video file
- `start` (float): Start time in the composition (seconds)
- `duration` (Optional[float]): Duration to use from the video (if None, uses full duration)
- `offset` (float): Start offset within the video file (seconds)

**Properties:**
- `fps` (float): Frames per second of the video
- `audio` (AudioClip): Audio track associated with this video

**Methods:**

#### subclip(start: float, end: float) -> VideoClip
Extract a subclip from this video.

**Parameters:**
- `start` (float): Start time within this clip (seconds)
- `end` (float): End time within this clip (seconds)

**Returns:** New VideoClip instance

**Raises:** ValueError if range is invalid

**Example:**
```python
clip = VideoClip("video.mp4")
segment = clip.subclip(10, 20)  # Extract seconds 10-20
```

---

#### loop(enabled: bool = True) -> Self
Enable or disable looping for this video clip.

**Parameters:**
- `enabled` (bool): Whether to enable looping

**Returns:** Self for chaining

**Example:**
```python
clip.loop(True)  # Video will restart when it reaches the end
```

---

#### set_offset(offset: float) -> Self
Set the offset within the source video file.

**Parameters:**
- `offset` (float): Offset in seconds

**Returns:** Self for chaining

---

### AlphaVideoClip

A video clip that loads and processes frames in BGRA format (with alpha channel).

Inherits from [VideoClip](#videoclip).

**Note:** AlphaVideoClip has a performance penalty (~33% more memory per frame) compared to VideoClip. Only use this when you need transparency support.

**Constructor:**
```python
AlphaVideoClip(
    path: str,
    start: float = 0,
    duration: Optional[float] = None,
    offset: float = 0
)
```

**Parameters:** Same as [VideoClip](#videoclip)

---

### ImageClip

An image clip that displays a static image for a given duration.

Inherits from [GraphicClip](#graphicclip).

**Constructor:**
```python
ImageClip(
    source: Union[str, np.ndarray],
    start: float = 0,
    duration: float = 5.0
)
```

**Parameters:**
- `source` (Union[str, np.ndarray]): Either a file path or a numpy array (RGB/RGBA)
- `start` (float): Start time in the composition (seconds)
- `duration` (float): How long to display the image (seconds)

**Class Methods:**

#### from_color(color: tuple, size: tuple, start: float = 0, duration: float = 5.0) -> ImageClip
Create a solid color image clip.

**Parameters:**
- `color` (tuple): RGB or RGBA tuple (0-255)
- `size` (tuple): (width, height)
- `start` (float): Start time in seconds
- `duration` (float): Duration in seconds

**Returns:** ImageClip instance

**Example:**
```python
# Create a red background
red_bg = ImageClip.from_color(
    color=(255, 0, 0),
    size=(1920, 1080),
    duration=10
)
```

---

### TextClip

A text clip that renders text using the pictex library.

Inherits from [GraphicClip](#graphicclip).

**Constructor:**
```python
TextClip(
    text: str,
    start: float = 0,
    duration: float = 5.0,
    canvas: Optional[Canvas] = None
)
```

**Parameters:**
- `text` (str): The text to render
- `start` (float): Start time in the composition (seconds)
- `duration` (float): How long to display the text (seconds)
- `canvas` (Optional[Canvas]): A pictex Canvas instance with styling configured

**Properties:**
- `text` (str): The text content

**Example:**
```python
from pictex import Canvas, LinearGradient, Shadow

canvas = (
    Canvas()
    .font_family("Arial")
    .font_size(60)
    .color("white")
    .padding(20)
    .background_color(LinearGradient(["#2C3E50", "#FD746C"]))
    .border_radius(10)
)

text = TextClip("Hello World", duration=3, canvas=canvas)
```

---

### AudioClip

An audio clip that can be overlaid on video.

Inherits from [MediaClip](#mediaclip).

**Constructor:**
```python
AudioClip(
    path: str,
    start: float = 0,
    duration: Optional[float] = None,
    volume: float = 1.0,
    offset: float = 0
)
```

**Parameters:**
- `path` (str): Path to the audio file
- `start` (float): Start time in the composition (seconds)
- `duration` (Optional[float]): Duration to use (if None, uses full audio duration)
- `volume` (float): Volume multiplier (0.0 to 1.0+)
- `offset` (float): Start offset within the audio file (seconds)

**Properties:**
- `path` (str): Path to the audio file
- `volume` (float): Volume multiplier
- `offset` (float): Offset within the source audio file
- `sample_rate` (int): Sample rate in Hz
- `channels` (int): Number of audio channels (1=mono, 2=stereo)
- `has_audio` (bool): Whether this clip has actual audio

**Methods:**

#### get_samples(start: float = 0, end: Optional[float] = None) -> np.ndarray
Get audio samples as numpy array.

**Parameters:**
- `start` (float): Start time relative to this clip's offset (seconds)
- `end` (Optional[float]): End time relative to this clip's offset (seconds)

**Returns:** Numpy array of shape (n_samples, n_channels) with float32 values in [-1, 1]

**Note:** For memory-efficient processing of long audio, use `iter_chunks()` instead.

---

#### iter_chunks(chunk_duration: float = 5.0) -> Iterator[Tuple[np.ndarray, float]]
Iterate over audio chunks sequentially.

**Parameters:**
- `chunk_duration` (float): Duration of each chunk in seconds

**Yields:** Tuple of (processed_samples, chunk_start_time)

**Example:**
```python
for samples, start_time in audio.iter_chunks(chunk_duration=10.0):
    # Process each chunk
    process_audio(samples)
```

---

#### add_transform(callback: Callable[[np.ndarray, float, int], np.ndarray]) -> Self
Apply a custom transformation to audio samples at render time.

**Parameters:**
- `callback` (Callable): Function that takes (samples, time, sample_rate) and returns transformed samples

**Returns:** Self for chaining

**Example:**
```python
def apply_reverb(samples, t, sr):
    # Apply custom reverb effect
    return reverb_filter(samples, sr)

audio.add_transform(apply_reverb)
```

---

#### fade_in(duration: float) -> Self
Apply a linear fade-in effect.

**Parameters:**
- `duration` (float): Fade duration in seconds

**Returns:** Self for chaining

---

#### fade_out(duration: float) -> Self
Apply a linear fade-out effect.

**Parameters:**
- `duration` (float): Fade duration in seconds

**Returns:** Self for chaining

---

#### set_volume(volume: float) -> Self
Set the volume of this audio clip.

**Parameters:**
- `volume` (float): Volume multiplier (0.0 to 1.0+)

**Returns:** Self for chaining

---

#### set_volume_curve(curve: Union[Callable[[float], float], float]) -> Self
Set a volume curve that changes over time.

**Parameters:**
- `curve`: Either a float (constant volume) or a function that takes time and returns volume

**Returns:** Self for chaining

**Example:**
```python
# Gradual volume increase
audio.set_volume_curve(lambda t: min(1.0, t / 5.0))
```

---

#### subclip(start: float, end: float) -> AudioClip
Extract a subclip from this audio.

**Parameters:**
- `start` (float): Start time within this clip (seconds)
- `end` (float): End time within this clip (seconds)

**Returns:** New AudioClip instance

---

#### loop(enabled: bool = True) -> Self
Enable or disable looping for this audio clip.

**Parameters:**
- `enabled` (bool): Whether to enable looping

**Returns:** Self for chaining

---

#### add_effect(effect: AudioEffect) -> Self
Apply an audio effect to this clip.

**Parameters:**
- `effect` (AudioEffect): An AudioEffect instance to apply

**Returns:** Self for chaining

**Example:**
```python
from movielite import afx
clip.add_effect(afx.FadeIn(2.0)).add_effect(afx.FadeOut(1.5))
```

---

### VideoWriter

Write clips to a video file.

**Constructor:**
```python
VideoWriter(
    output_path: str,
    fps: float = 30,
    size: Optional[Tuple[int, int]] = None,
    duration: Optional[float] = None
)
```

**Parameters:**
- `output_path` (str): Path where the final video will be saved
- `fps` (float): Frames per second for the output video
- `size` (Optional[Tuple[int, int]]): Video dimensions (width, height). If None, auto-calculated from clips
- `duration` (Optional[float]): Total duration in seconds. If None, auto-calculated from clips

**Methods:**

#### add_clip(clip: MediaClip) -> VideoWriter
Add a media clip to the composition.

**Parameters:**
- `clip` (MediaClip): MediaClip to add (VideoClip, AudioClip, ImageClip, TextClip, etc.)

**Returns:** Self for chaining

---

#### add_clips(clips: List[MediaClip]) -> VideoWriter
Add multiple media clips to the composition.

**Parameters:**
- `clips` (List[MediaClip]): List of MediaClip instances to add

**Returns:** Self for chaining

---

#### write(processes: int = 1, video_quality: VideoQuality = VideoQuality.MIDDLE) -> None
Render and write the final video.

**Parameters:**
- `processes` (int): Number of processes to use for parallel rendering
- `video_quality` (VideoQuality): Quality preset for encoding

**Example:**
```python
from movielite import VideoWriter, VideoQuality

writer = VideoWriter("output.mp4", fps=30, size=(1920, 1080))
writer.add_clip(clip)
writer.write(processes=8, video_quality=VideoQuality.HIGH)
```

---

## Visual Effects (vfx)

All visual effects inherit from `GraphicEffect` and are applied using `clip.add_effect(effect)`.

### Fade Effects

#### FadeIn
Gradually increases opacity from 0 to the clip's original opacity.

```python
from movielite import vfx
clip.add_effect(vfx.FadeIn(duration=2.0))
```

**Parameters:**
- `duration` (float): Duration of the fade in seconds

---

#### FadeOut
Gradually decreases opacity from the clip's original opacity to 0.

```python
clip.add_effect(vfx.FadeOut(duration=1.5))
```

**Parameters:**
- `duration` (float): Duration of the fade in seconds

---

### Blur Effects

#### Blur
Apply Gaussian blur to the clip.

```python
clip.add_effect(vfx.Blur(intensity=5.0, animated=False))
```

**Parameters:**
- `intensity` (float): Blur intensity (kernel size). Higher = more blur
- `animated` (bool): If True, blur increases from 0 to intensity over duration
- `duration` (Optional[float]): Duration of the blur animation (required if animated=True)

---

#### BlurIn
Starts blurred and gradually becomes sharp.

```python
clip.add_effect(vfx.BlurIn(duration=2.0, max_intensity=15.0))
```

**Parameters:**
- `duration` (float): Duration of the blur-in effect
- `max_intensity` (float): Maximum blur intensity at the start

---

#### BlurOut
Starts sharp and gradually becomes blurred.

```python
clip.add_effect(vfx.BlurOut(duration=2.0, max_intensity=15.0))
```

**Parameters:**
- `duration` (float): Duration of the blur-out effect
- `max_intensity` (float): Maximum blur intensity at the end

---

### Color Effects

#### Saturation
Adjust saturation of the clip.

```python
clip.add_effect(vfx.Saturation(factor=1.5))
```

**Parameters:**
- `factor` (float): Saturation multiplier (0.0=grayscale, 1.0=no change, >1.0=more saturated)

---

#### Brightness
Adjust brightness of the clip.

```python
clip.add_effect(vfx.Brightness(factor=1.2))
```

**Parameters:**
- `factor` (float): Brightness multiplier (1.0=no change, >1.0=brighter, <1.0=darker)

---

#### Contrast
Adjust contrast of the clip.

```python
clip.add_effect(vfx.Contrast(factor=1.3))
```

**Parameters:**
- `factor` (float): Contrast multiplier (1.0=no change, >1.0=more contrast, <1.0=less contrast)

---

#### BlackAndWhite / Grayscale
Convert clip to black and white.

```python
clip.add_effect(vfx.BlackAndWhite())
# or
clip.add_effect(vfx.Grayscale())
```

---

#### Sepia
Apply sepia tone effect.

```python
clip.add_effect(vfx.Sepia(intensity=1.0))
```

**Parameters:**
- `intensity` (float): Intensity of the sepia effect (0.0 to 1.0)

---

### Zoom Effects

#### ZoomIn
Gradually scales up the clip from a smaller size.

```python
clip.add_effect(vfx.ZoomIn(duration=3.0, from_scale=0.5, to_scale=1.0))
```

**Parameters:**
- `duration` (float): Duration of the zoom effect
- `from_scale` (float): Starting scale (0.5 = 50% size)
- `to_scale` (float): Ending scale (1.0 = 100% size)

---

#### ZoomOut
Gradually scales down the clip.

```python
clip.add_effect(vfx.ZoomOut(duration=3.0, from_scale=1.0, to_scale=0.5))
```

**Parameters:**
- `duration` (float): Duration of the zoom effect
- `from_scale` (float): Starting scale
- `to_scale` (float): Ending scale

---

#### KenBurns
Slow zoom and pan animation for cinematic effect.

```python
clip.add_effect(vfx.KenBurns(
    duration=None,  # Uses entire clip duration
    start_scale=1.0,
    end_scale=1.2,
    start_position=(0, 0),
    end_position=(100, 50)
))
```

**Parameters:**
- `duration` (Optional[float]): Duration of the effect (None = entire clip duration)
- `start_scale` (float): Starting zoom level
- `end_scale` (float): Ending zoom level
- `start_position` (Tuple[int, int]): Starting position (x, y)
- `end_position` (Tuple[int, int]): Ending position (x, y)

---

### Glitch Effects

#### Glitch
Digital distortion artifacts simulating VHS glitches.

```python
clip.add_effect(vfx.Glitch(
    intensity=0.5,
    rgb_shift=True,
    horizontal_lines=True,
    scan_lines=False
))
```

**Parameters:**
- `intensity` (float): Intensity of the glitch effect (0.0 to 1.0)
- `rgb_shift` (bool): Enable RGB channel shifting
- `horizontal_lines` (bool): Enable horizontal displacement lines
- `scan_lines` (bool): Enable scan line artifacts

---

#### ChromaticAberration
RGB channel separation for lens distortion effect.

```python
clip.add_effect(vfx.ChromaticAberration(intensity=5.0))
```

**Parameters:**
- `intensity` (float): Intensity of the aberration in pixels

---

#### Pixelate
Reduce resolution to create a blocky appearance.

```python
clip.add_effect(vfx.Pixelate(block_size=10))
```

**Parameters:**
- `block_size` (int): Size of pixelation blocks in pixels

---

### Other Effects

#### Vignette
Darken the edges of the frame.

```python
clip.add_effect(vfx.Vignette(intensity=0.5, radius=0.8))
```

**Parameters:**
- `intensity` (float): Darkness intensity at the edges (0.0 to 1.0)
- `radius` (float): Radius of the bright center area (0.0 to 1.0)

---

## Audio Effects (afx)

All audio effects inherit from `AudioEffect` and are applied using `audio.add_effect(effect)`.

### FadeIn
Gradually increases volume from 0 to the clip's original volume.

```python
from movielite import afx
audio.add_effect(afx.FadeIn(duration=2.0))
```

**Parameters:**
- `duration` (float): Duration of the fade in seconds

---

### FadeOut
Gradually decreases volume from the clip's original volume to 0.

```python
audio.add_effect(afx.FadeOut(duration=1.5))
```

**Parameters:**
- `duration` (float): Duration of the fade in seconds

---

## Transitions (vtx)

All transitions inherit from `Transition` and are applied using `clip1.add_transition(clip2, transition)`.

### CrossFade
Smooth opacity-based transition between two clips.

```python
from movielite import vtx
clip1.add_transition(clip2, vtx.CrossFade(duration=0.5))
```

**Parameters:**
- `duration` (float): Duration of the crossfade in seconds

**Note:** Requires clips to overlap by at least `duration` seconds.

---

### BlurDissolve
Transition with blur effect during the dissolve.

```python
clip1.add_transition(clip2, vtx.BlurDissolve(duration=1.0, max_blur=15.0))
```

**Parameters:**
- `duration` (float): Duration of the transition in seconds
- `max_blur` (float): Maximum blur intensity at the midpoint

---

## Enumerations

### VideoQuality

Quality presets for video encoding.

```python
from movielite import VideoQuality

# Available values:
VideoQuality.LOW         # Fastest encoding, lowest quality
VideoQuality.MIDDLE      # Balanced (default)
VideoQuality.HIGH        # Slower encoding, better quality
VideoQuality.VERY_HIGH   # Slowest encoding, best quality
```

---

## Utilities

### get_logger()
Get the movielite logger instance.

```python
from movielite import get_logger

logger = get_logger()
logger.info("Processing video...")
```

---

### set_log_level(level: int)
Set logging level.

```python
from movielite import set_log_level
import logging

set_log_level(logging.DEBUG)
```

**Parameters:**
- `level` (int): Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING)
