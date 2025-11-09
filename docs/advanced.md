# Advanced Usage Guide

This guide covers advanced topics for using movielite effectively.

## Table of Contents

- [Custom Effect Development](#custom-effect-development)
- [Performance Optimization](#performance-optimization)
- [Memory Management](#memory-management)
- [Advanced Audio Processing](#advanced-audio-processing)
- [Complex Compositions](#complex-compositions)
- [Masking and Compositing](#masking-and-compositing)
- [Integration with Other Libraries](#integration-with-other-libraries)

---

## Custom Effect Development

### Creating Custom Visual Effects

You can create custom visual effects by subclassing `GraphicEffect`:

```python
from movielite.vfx.base import GraphicEffect
from movielite.core import GraphicClip
import cv2
import numpy as np

class CustomVignetteEffect(GraphicEffect):
    """Custom vignette effect with adjustable parameters."""

    def __init__(self, intensity: float = 0.7, color: tuple = (0, 0, 0)):
        """
        Args:
            intensity: Darkness intensity (0.0 to 1.0)
            color: RGB color tuple for vignette (default: black)
        """
        self.intensity = intensity
        self.color = color

    def apply(self, clip: GraphicClip) -> None:
        """Apply the vignette effect to the clip."""

        # Cache the vignette mask
        cache = {}

        def vignette_transform(frame: np.ndarray, t: float) -> np.ndarray:
            h, w = frame.shape[:2]
            cache_key = (w, h)

            if cache_key not in cache:
                # Create radial gradient
                center_x, center_y = w // 2, h // 2
                Y, X = np.ogrid[:h, :w]
                dist = np.sqrt(((X - center_x) / w) ** 2 + ((Y - center_y) / h) ** 2)

                # Create mask
                mask = np.clip(1.0 - dist, 0, 1)
                mask = 1.0 - (1.0 - mask) * self.intensity
                mask = np.stack([mask] * 3, axis=2)

                cache[cache_key] = mask

            # Apply vignette
            result = frame.astype(np.float32) * cache[cache_key]
            return result.astype(np.uint8)

        clip.add_transform(vignette_transform)

# Usage
from movielite import VideoClip, VideoWriter

clip = VideoClip("video.mp4")
clip.add_effect(CustomVignetteEffect(intensity=0.8, color=(20, 20, 30)))

writer = VideoWriter("output.mp4", fps=clip.fps, size=clip.size)
writer.add_clip(clip)
writer.write()
clip.close()
```

### Creating Custom Audio Effects

```python
from movielite.afx.base import AudioEffect
from movielite.audio import AudioClip
import numpy as np

class EchoEffect(AudioEffect):
    """Add echo effect to audio."""

    def __init__(self, delay: float = 0.3, decay: float = 0.5):
        """
        Args:
            delay: Echo delay in seconds
            decay: Echo decay factor (0.0 to 1.0)
        """
        self.delay = delay
        self.decay = decay

    def apply(self, clip: AudioClip) -> None:
        """Apply echo effect to the audio clip."""

        def echo_transform(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
            # Calculate delay in samples
            delay_samples = int(self.delay * sr)

            # Create echo buffer
            result = samples.copy()

            # Add delayed and decayed samples
            if len(samples) > delay_samples:
                result[delay_samples:] += samples[:-delay_samples] * self.decay

            # Normalize to prevent clipping
            max_val = np.abs(result).max()
            if max_val > 1.0:
                result = result / max_val

            return result

        clip.add_transform(echo_transform)

# Usage
from movielite import AudioClip

audio = AudioClip("audio.mp3")
audio.add_effect(EchoEffect(delay=0.5, decay=0.4))
```

### Creating Custom Transitions

```python
from movielite.vtx.base import Transition
from movielite.core import GraphicClip

class SlideTransition(Transition):
    """Slide transition between two clips."""

    def __init__(self, duration: float, direction: str = "left"):
        """
        Args:
            duration: Duration of the transition
            direction: Slide direction ("left", "right", "up", "down")
        """
        self.duration = duration
        self.direction = direction

    def apply(self, clip1: GraphicClip, clip2: GraphicClip) -> None:
        """Apply slide transition."""

        # Validate overlap
        self._validate_clips_have_overlap(clip1, clip2, self.duration)

        # Get overlap region
        overlap_start = clip2.start
        overlap_end = min(clip1.end, clip2.start + self.duration)

        # Modify clip positions
        original_pos1 = clip1._position
        original_pos2 = clip2._position

        def position_func_clip1(t):
            base_pos = original_pos1(t)

            if clip1.start <= t < overlap_end:
                # During transition, slide out
                progress = (t - overlap_start) / self.duration

                if self.direction == "left":
                    offset_x = int(-clip1.size[0] * progress)
                    return (base_pos[0] + offset_x, base_pos[1])
                elif self.direction == "right":
                    offset_x = int(clip1.size[0] * progress)
                    return (base_pos[0] + offset_x, base_pos[1])

            return base_pos

        def position_func_clip2(t):
            base_pos = original_pos2(t)

            if overlap_start <= t < overlap_end:
                # During transition, slide in
                progress = (t - overlap_start) / self.duration

                if self.direction == "left":
                    offset_x = int(clip2.size[0] * (1 - progress))
                    return (base_pos[0] + offset_x, base_pos[1])
                elif self.direction == "right":
                    offset_x = int(-clip2.size[0] * (1 - progress))
                    return (base_pos[0] + offset_x, base_pos[1])

            return base_pos

        clip1.set_position(position_func_clip1)
        clip2.set_position(position_func_clip2)
```

---

## Performance Optimization

### Using Multiprocessing

For long videos, use multiprocessing to parallelize rendering:

```python
from movielite import VideoClip, VideoWriter, VideoQuality
import multiprocessing

clip = VideoClip("long_video.mp4")

writer = VideoWriter("output.mp4", fps=clip.fps, size=clip.size)
writer.add_clip(clip)

# Use all available CPU cores
num_processes = multiprocessing.cpu_count()
writer.write(processes=num_processes, video_quality=VideoQuality.HIGH)

clip.close()
```

### Caching Expensive Computations

For static transformations, cache results:

```python
import cv2
import numpy as np

class CachedGrayscaleEffect:
    def __init__(self):
        self.cache = {}

    def __call__(self, frame: np.ndarray, t: float) -> np.ndarray:
        # Use frame memory address as cache key
        frame_id = id(frame)

        if frame_id not in self.cache:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            self.cache[frame_id] = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # Warning: you should have a maximum amount of frames stored in your cache
        return self.cache[frame_id]

clip.add_transform(CachedGrayscaleEffect())
```

---

## Advanced Audio Processing

### Complex Audio Mixing

```python
from movielite import AudioClip, VideoClip, VideoWriter, afx
import numpy as np

# Load multiple audio tracks
video = VideoClip("video.mp4")
music = AudioClip("background_music.mp3", start=0, volume=0.3)
narration = AudioClip("voiceover.mp3", start=5, volume=1.0)
sfx1 = AudioClip("explosion.wav", start=10, volume=0.8)
sfx2 = AudioClip("applause.wav", start=15, volume=0.6)

# Apply effects to each track
music.add_effect(afx.FadeIn(2.0)).add_effect(afx.FadeOut(3.0))
narration.add_effect(afx.FadeIn(0.5))

# Duck music during narration (custom volume curve)
def ducking_curve(t):
    if 5 <= t < 25:  # Narration period
        return 0.2  # Reduce music to 20%
    return 0.5  # Normal music at 50%

music.set_volume_curve(ducking_curve)

# Mix all tracks
writer = VideoWriter("output.mp4", fps=video.fps, size=video.size)
writer.add_clip(video)
writer.add_clip(music)
writer.add_clip(narration)
writer.add_clip(sfx1)
writer.add_clip(sfx2)
writer.write()

video.close()
```

### Custom Audio Filters

```python
import numpy as np
from scipy import signal

def apply_lowpass_filter(cutoff_freq: float = 1000, order: int = 5):
    """Create a lowpass filter transform."""

    def lowpass_transform(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
        # Design Butterworth lowpass filter
        nyquist = sr / 2
        normal_cutoff = cutoff_freq / nyquist
        b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)

        # Apply filter to each channel
        filtered = np.zeros_like(samples)
        for ch in range(samples.shape[1]):
            filtered[:, ch] = signal.lfilter(b, a, samples[:, ch])

        return filtered

    return lowpass_transform

# Usage
audio = AudioClip("audio.mp3")
audio.add_transform(apply_lowpass_filter(cutoff_freq=2000, order=4))
```

---

## Complex Compositions

### Picture-in-Picture Effect

```python
from movielite import VideoClip, VideoWriter, vfx

# Main video
main_video = VideoClip("main.mp4", start=0)

# Small overlay video
pip_video = VideoClip("overlay.mp4", start=0)
pip_video.set_size(width=320, height=180)  # Resize to small size
pip_video.set_position((main_video.size[0] - 340, 20))  # Top-right corner
pip_video.add_effect(vfx.FadeIn(0.5))
pip_video.add_effect(vfx.FadeOut(0.5))

# Compose
writer = VideoWriter("output.mp4", fps=30, size=main_video.size)
writer.add_clip(main_video)
writer.add_clip(pip_video)
writer.write()

main_video.close()
pip_video.close()
```

### Split Screen

```python
from movielite import VideoClip, VideoWriter, ImageClip

# Create black background
bg = ImageClip.from_color((0, 0, 0), size=(1920, 1080), duration=10)

# Left video
left_video = VideoClip("left.mp4")
left_video.set_size(width=960, height=1080)
left_video.set_position((0, 0))

# Right video
right_video = VideoClip("right.mp4")
right_video.set_size(width=960, height=1080)
right_video.set_position((960, 0))

# Compose
writer = VideoWriter("split_screen.mp4", fps=30, size=(1920, 1080))
writer.add_clip(bg)
writer.add_clip(left_video)
writer.add_clip(right_video)
writer.write()

left_video.close()
right_video.close()
```

### Animated Text

```python
from movielite import VideoClip, TextClip, VideoWriter
from pictex import Canvas
import math

video = VideoClip("background.mp4")

canvas = Canvas().font_size(80).color("white").background_color("transparent")
text = TextClip("Animated Title", start=0, duration=5, canvas=canvas)

# Animate position (bounce effect)
def animated_position(t):
    # Bounce in from top
    if t < 1.0:
        y = int(-100 + (video.size[1] // 2) * (1 - math.cos(t * math.pi)))
    else:
        y = video.size[1] // 2

    x = video.size[0] // 2 - text.size[0] // 2
    return (x, y)

text.set_position(animated_position)

# Animate opacity
text.set_opacity(lambda t: min(1.0, t / 0.5))

writer = VideoWriter("output.mp4", fps=video.fps, size=video.size)
writer.add_clip(video)
writer.add_clip(text)
writer.write()

video.close()
```

---

## Integration with Other Libraries

### Using OpenCV Filters

```python
import cv2
import numpy as np
from movielite import VideoClip, VideoWriter

clip = VideoClip("video.mp4")

def apply_bilateral_filter(frame: np.ndarray, t: float) -> np.ndarray:
    """Apply bilateral filter for edge-preserving smoothing."""
    return cv2.bilateralFilter(frame, d=9, sigmaColor=75, sigmaSpace=75)

clip.add_transform(apply_bilateral_filter)

writer = VideoWriter("filtered.mp4", fps=clip.fps, size=clip.size)
writer.add_clip(clip)
writer.write()
clip.close()
```

### Using NumPy for Advanced Effects

```python
import numpy as np
from movielite import VideoClip, VideoWriter

clip = VideoClip("video.mp4")

def color_temperature_shift(frame: np.ndarray, t: float) -> np.ndarray:
    """Shift color temperature (warmer)."""
    result = frame.copy().astype(np.float32)

    # Increase red channel
    result[:, :, 2] = np.clip(result[:, :, 2] * 1.1, 0, 255)

    # Decrease blue channel
    result[:, :, 0] = np.clip(result[:, :, 0] * 0.9, 0, 255)

    return result.astype(np.uint8)

clip.add_transform(color_temperature_shift)

writer = VideoWriter("warm.mp4", fps=clip.fps, size=clip.size)
writer.add_clip(clip)
writer.write()
clip.close()
```

### Using Pillow for Image Processing

```python
from PIL import Image, ImageEnhance
import numpy as np
from movielite import VideoClip, VideoWriter
import cv2

clip = VideoClip("video.mp4")

def enhance_colors(frame: np.ndarray, t: float) -> np.ndarray:
    """Use Pillow to enhance colors."""
    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Convert to PIL Image
    pil_image = Image.fromarray(rgb_frame)

    # Enhance color
    enhancer = ImageEnhance.Color(pil_image)
    enhanced = enhancer.enhance(1.5)  # 1.5x color saturation

    # Convert back to numpy array (BGR)
    rgb_array = np.array(enhanced)
    return cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)

clip.add_transform(enhance_colors)

writer = VideoWriter("enhanced.mp4", fps=clip.fps, size=clip.size)
writer.add_clip(clip)
writer.write()
clip.close()
```

### Using scipy for Audio Processing

```python
from scipy.signal import butter, filtfilt
import numpy as np
from movielite import AudioClip

def bandpass_filter(lowcut: float, highcut: float, order: int = 5):
    """Create a bandpass filter for audio."""

    def filter_transform(samples: np.ndarray, t: float, sr: int) -> np.ndarray:
        nyquist = sr / 2
        low = lowcut / nyquist
        high = highcut / nyquist

        b, a = butter(order, [low, high], btype='band')

        filtered = np.zeros_like(samples)
        for ch in range(samples.shape[1]):
            filtered[:, ch] = filtfilt(b, a, samples[:, ch])

        return filtered

    return filter_transform

audio = AudioClip("audio.mp3")
audio.add_transform(bandpass_filter(lowcut=200, highcut=3000))
```

---

## Masking and Compositing

Masking is a powerful feature for creating advanced compositing effects where one clip's visibility is controlled by another clip's luminance values.

### Basic Masking

```python
from movielite import VideoClip, ImageClip, VideoWriter

video = VideoClip("waves.mp4")
mask = ImageClip("mask.png", duration=video.duration)

# Apply mask - white areas of mask = visible, black = transparent
video.set_mask(mask)

writer = VideoWriter("masked.mp4", fps=video.fps, size=video.size)
writer.add_clip(video)
writer.write()

video.close()
```

### Text Masking

```python
from movielite import VideoClip, TextClip, VideoWriter
from pictex import Canvas

video = VideoClip("colorful.mp4", duration=5)

# Create text as mask
canvas = Canvas().font_size(200).color("white").background_color("transparent")
text = TextClip("MASKED", duration=5, canvas=canvas)
text.set_position((video.size[0] // 2 - text.size[0] // 2,
                   video.size[1] // 2 - text.size[1] // 2))

# Video only visible through text
video.set_mask(text)

writer = VideoWriter("text_masked.mp4", fps=video.fps, size=video.size)
writer.add_clip(video)
writer.write()

video.close()
```

### Animated Masks

```python
import numpy as np
from movielite import VideoClip, TextClip, VideoWriter
from pictex import Canvas

video = VideoClip("waves.mp4", duration=10)

# Create animated text mask
canvas = Canvas().font_size(200).color("white").background_color("transparent")
text = TextClip("Hello World!", duration=10, canvas=canvas)

# Animate position (wave motion)
text.set_position(lambda t: (
    960 - text.size[0] // 2,
    500 + int(20 * np.sin(2 * np.pi * (t / 10.0)))
))

# Animate scale (grow)
text.set_scale(lambda t: 1.0 + 0.4 * (t / 10.0))

video.set_mask(text)
video.set_size(1920, 1080)

writer = VideoWriter("animated_mask.mp4", fps=30, size=(1920, 1080))
writer.add_clip(video)
writer.write()

video.close()
```

---

## Best Practices

1. **Profile your effects**: Time-intensive effects should be optimized or cached.

2. **Use appropriate data types**: Keep frames as uint8 until final processing to save memory.

3. **Leverage multiprocessing**: For videos longer than 60 seconds, use multiple processes if is possible.

4. **Cache static transformations**: If a transformation doesn't depend on time, cache its result.
