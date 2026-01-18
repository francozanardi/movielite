"""
Examples demonstrating the rotation feature in movielite.

Rotation can be applied via:
- clip.set_rotation(angle)  - Convenience method
- clip.add_effect(vfx.Rotation(angle))  - Using the VFX directly
"""
import math
from movielite import ImageClip, VideoWriter, vfx


# Example 1: Static rotation
def example_static_rotation():
    """Basic static rotation - rotate an image by a fixed angle."""
    image = ImageClip("sample.png", start=0, duration=3.0)
    image.set_rotation(45)  # 45 degrees counter-clockwise
    
    writer = VideoWriter("rotation_static.mp4", fps=30)
    writer.add_clip(image)
    writer.write()


# Example 2: Animated rotation (spinning)
def example_animated_rotation():
    """Animated rotation using a function of time."""
    image = ImageClip("sample.png", start=0, duration=5.0)
    
    # 72 degrees per second = full rotation in 5 seconds
    image.set_rotation(lambda t: t * 72, expand=False)
    
    writer = VideoWriter("rotation_animated.mp4", fps=30)
    writer.add_clip(image)
    writer.write()


# Example 3: Rotation with radians and high-quality resampling
def example_radians_and_resample():
    """Using radians and bicubic interpolation for best quality."""
    image = ImageClip("sample.png", start=0, duration=3.0)
    
    # Rotate by pi/4 radians (45 degrees) with high-quality resampling
    image.set_rotation(math.pi / 4, unit="rad", resample="bicubic")
    
    writer = VideoWriter("rotation_radians.mp4", fps=30)
    writer.add_clip(image)
    writer.write()


# Example 4: Custom center and translate
def example_center_and_translate():
    """Rotate around a custom point with post-rotation translation."""
    image = ImageClip("sample.png", start=0, duration=4.0)
    
    # Rotate around top-left corner (0, 0), then translate to center it
    image.set_rotation(
        lambda t: t * 90,  # 90 degrees per second
        center=(0, 0),
        translate=(200, 200),  # Shift the result
        expand=True
    )
    
    writer = VideoWriter("rotation_center_translate.mp4", fps=30)
    writer.add_clip(image)
    writer.write()


# Example 5: Using the VFX directly with background color
def example_vfx_with_bg_color():
    """Using vfx.Rotation directly with a custom background color."""
    image = ImageClip("sample.png", start=0, duration=3.0)
    
    # Use VFX directly with custom background color (BGR format)
    image.add_effect(vfx.Rotation(
        angle=30,
        expand=True,
        bg_color=(255, 200, 100)  # Light blue in BGR
    ))
    
    writer = VideoWriter("rotation_bg_color.mp4", fps=30)
    writer.add_clip(image)
    writer.write()


if __name__ == "__main__":
    print("Rotation Examples")
    print("=================")
    print("1. example_static_rotation() - Basic fixed angle rotation")
    print("2. example_animated_rotation() - Time-based spinning")
    print("3. example_radians_and_resample() - Radians + bicubic quality")
    print("4. example_center_and_translate() - Custom pivot point")
    print("5. example_vfx_with_bg_color() - VFX with background color")
    print()
    
    # Uncomment to run:
    # example_static_rotation()
    # example_animated_rotation()
    # example_radians_and_resample()
    # example_center_and_translate()
    # example_vfx_with_bg_color()
