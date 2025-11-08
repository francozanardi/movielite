"""
Masking examples using movielite.

Demonstrates various masking techniques for advanced compositing effects.
"""

import numpy as np
from movielite import VideoClip, ImageClip, TextClip, VideoWriter, VideoQuality, vfx
from pictex import Canvas


def example_simple_image_mask():
    """Apply a simple image mask to a video."""
    print("Example 1: Simple image mask")

    video = VideoClip("input.mp4", start=0, duration=5)
    mask = ImageClip("mask.png", duration=5)

    video.set_mask(mask)

    writer = VideoWriter("output_image_mask.mp4", fps=video.fps, size=video.size)
    writer.add_clip(video)
    writer.write()

    video.close()
    print("Created output_image_mask.mp4\n")


def example_text_mask_static():
    """Video visible only through text shape."""
    print("Example 2: Static text mask")

    video = VideoClip("waves.mp4", start=0, duration=5)

    # Create text as mask
    canvas = Canvas().font_size(200).color("white").background_color("transparent")
    text = TextClip("MASKED", start=0, duration=5, canvas=canvas)
    text.set_position((video.size[0] // 2 - text.size[0] // 2, video.size[1] // 2 - text.size[1] // 2))

    # Apply mask
    video.set_mask(text)

    writer = VideoWriter("output_text_mask.mp4", fps=video.fps, size=video.size)
    writer.add_clip(video)
    writer.write()

    video.close()
    print("Created output_text_mask.mp4\n")


def example_animated_text_mask():
    """Animated text mask with moving position and scaling."""
    print("Example 3: Animated text mask")

    video = VideoClip("waves.mp4", start=0, duration=10)

    # Create animated text mask
    canvas = Canvas().font_size(200).color("white").background_color("transparent")
    text = TextClip("Hello World!", start=0, duration=10, canvas=canvas)

    # Animate position (sinusoidal wave motion)
    text.set_position(lambda t: (
        960 - text.size[0] // 2,
        500 + int(20 * np.sin(2 * np.pi * (t / text.duration)))
    ))

    # Animate scale (grow over time)
    text.set_scale(lambda t: 1.0 + 0.4 * (t / text.duration))

    # Apply mask
    video.set_mask(text)
    video.set_size(1920, 1080)

    writer = VideoWriter("output_animated_text_mask.mp4", fps=30, size=(1920, 1080))
    writer.add_clip(video)
    writer.write()

    video.close()
    print("Created output_animated_text_mask.mp4\n")


def example_shape_mask():
    """Create a custom shape mask using solid colors."""
    print("Example 4: Shape mask")

    video = VideoClip("input.mp4", start=0, duration=5)

    # Create a circular gradient mask
    # White in center, black at edges
    import cv2

    mask_size = video.size
    mask_frame = np.zeros((mask_size[1], mask_size[0]), dtype=np.uint8)

    center = (mask_size[0] // 2, mask_size[1] // 2)
    radius = min(mask_size[0], mask_size[1]) // 3

    # Draw white circle
    cv2.circle(mask_frame, center, radius, 255, -1)

    # Apply Gaussian blur for soft edges
    mask_frame = cv2.GaussianBlur(mask_frame, (51, 51), 0)

    # Convert to RGB
    mask_rgb = cv2.cvtColor(mask_frame, cv2.COLOR_GRAY2RGB)

    # Create ImageClip from array
    mask = ImageClip(mask_rgb, duration=5)

    video.set_mask(mask)

    writer = VideoWriter("output_shape_mask.mp4", fps=video.fps, size=video.size)
    writer.add_clip(video)
    writer.write()

    video.close()
    print("Created output_shape_mask.mp4\n")


if __name__ == "__main__":
    print("=== Masking Effects Examples ===\n")

    # Uncomment the examples you want to run
    # example_simple_image_mask()
    # example_text_mask_static()
    # example_animated_text_mask()
    # example_shape_mask()

    print("Done!")
