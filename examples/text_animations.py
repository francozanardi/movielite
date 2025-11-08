"""
Text animation examples using movielite and pictex.

Demonstrates various text overlay techniques and animations.
"""

from movielite import VideoClip, TextClip, ImageClip, VideoWriter, VideoQuality, vfx
from pictex import Canvas, LinearGradient, Shadow
import math


def example_simple_text():
    """Add simple static text overlay."""
    print("Example 1: Simple text")

    video = VideoClip("input.mp4")

    canvas = Canvas().font_size(60).color("white").background_color("transparent")
    text = TextClip("Hello World", start=0, duration=5, canvas=canvas)
    text.set_position((video.size[0] // 2 - text.size[0] // 2, 100))

    writer = VideoWriter("output_simple_text.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, text])
    writer.write()

    video.close()
    print("Created output_simple_text.mp4\n")


def example_styled_text():
    """Add styled text with gradient and shadow."""
    print("Example 2: Styled text")

    video = VideoClip("input.mp4")

    canvas = (
        Canvas()
        .font_family("Arial")
        .font_size(80)
        .color("white")
        .padding(30)
        .background_color(LinearGradient(["#FF6B6B", "#4ECDC4"]))
        .border_radius(15)
        .text_shadows(Shadow(offset=(3, 3), blur_radius=5, color="black"))
    )

    text = TextClip("Styled Title", start=0, duration=5, canvas=canvas)
    text.set_position((video.size[0] // 2 - text.size[0] // 2, 200))

    writer = VideoWriter("output_styled_text.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, text])
    writer.write()

    video.close()
    print("Created output_styled_text.mp4\n")


def example_fade_text():
    """Text with fade in and fade out."""
    print("Example 3: Fade text")

    video = VideoClip("input.mp4")

    canvas = Canvas().font_size(70).color("white").background_color("transparent")
    text = TextClip("Fading Text", start=2, duration=4, canvas=canvas)
    text.set_position((video.size[0] // 2 - text.size[0] // 2, 300))
    text.add_effect(vfx.FadeIn(1.0))
    text.add_effect(vfx.FadeOut(1.0))

    writer = VideoWriter("output_fade_text.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, text])
    writer.write()

    video.close()
    print("Created output_fade_text.mp4\n")


def example_animated_position():
    """Text with animated position (sliding in from left)."""
    print("Example 4: Animated position")

    video = VideoClip("input.mp4")

    canvas = Canvas().font_size(60).color("white").padding(20).background_color("#333333")
    text = TextClip("Sliding Text", start=0, duration=5, canvas=canvas)

    # Slide in from left over 2 seconds
    def animated_position(t):
        if t < 2.0:
            # Slide in from left
            x = int(-text.size[0] + (text.size[0] + video.size[0] // 2) * (t / 2.0))
        else:
            # Stay centered
            x = video.size[0] // 2 - text.size[0] // 2

        y = video.size[1] // 2 - text.size[1] // 2
        return (x, y)

    text.set_position(animated_position)

    writer = VideoWriter("output_animated_pos.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, text])
    writer.write()

    video.close()
    print("Created output_animated_pos.mp4\n")


def example_bouncing_text():
    """Text with bouncing animation."""
    print("Example 5: Bouncing text")

    video = VideoClip("input.mp4")

    canvas = Canvas().font_size(80).color("#FFD700").background_color("transparent")
    text = TextClip("Bounce!", start=0, duration=6, canvas=canvas)

    # Bounce effect
    def bounce_position(t):
        x = video.size[0] // 2 - text.size[0] // 2

        # Bounce amplitude decreases over time
        amplitude = 200 * (1.0 - t / 6.0)
        frequency = 3.0
        y = int(video.size[1] // 2 - text.size[1] // 2 - abs(math.sin(t * frequency * math.pi)) * amplitude)

        return (x, y)

    text.set_position(bounce_position)

    writer = VideoWriter("output_bounce.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, text])
    writer.write()

    video.close()
    print("Created output_bounce.mp4\n")


def example_scaling_text():
    """Text with animated scale (zooming in)."""
    print("Example 6: Scaling text")

    video = VideoClip("input.mp4")

    canvas = Canvas().font_size(70).color("white").background_color("transparent")
    text = TextClip("ZOOM IN", start=0, duration=3, canvas=canvas)
    text.set_position((video.size[0] // 2 - text.size[0] // 2, video.size[1] // 2 - text.size[1] // 2))

    # Zoom from 0.5x to 1.5x over 3 seconds
    text.set_scale(lambda t: 0.5 + (1.0 * (t / 3.0)))

    writer = VideoWriter("output_zoom_text.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, text])
    writer.write()

    video.close()
    print("Created output_zoom_text.mp4\n")


def example_multiple_text_layers():
    """Multiple text layers with different timings."""
    print("Example 7: Multiple text layers")

    video = VideoClip("input.mp4")

    # Title (appears first)
    canvas1 = Canvas().font_size(90).color("white").background_color(LinearGradient(["#FF6B6B", "#FF8E53"]))
    title = TextClip("Title", start=0, duration=3, canvas=canvas1)
    title.set_position((video.size[0] // 2 - title.size[0] // 2, 100))
    title.add_effect(vfx.FadeIn(0.5))
    title.add_effect(vfx.FadeOut(0.5))

    # Subtitle (appears after title)
    canvas2 = Canvas().font_size(50).color("#CCCCCC").background_color("transparent")
    subtitle = TextClip("Subtitle text here", start=1, duration=4, canvas=canvas2)
    subtitle.set_position((video.size[0] // 2 - subtitle.size[0] // 2, 220))
    subtitle.add_effect(vfx.FadeIn(0.5))
    subtitle.add_effect(vfx.FadeOut(0.5))

    # Caption (appears last)
    canvas3 = Canvas().font_size(40).color("yellow").background_color("transparent")
    caption = TextClip("Additional info", start=2.5, duration=3, canvas=canvas3)
    caption.set_position((video.size[0] // 2 - caption.size[0] // 2, video.size[1] - 100))
    caption.add_effect(vfx.FadeIn(0.3))
    caption.add_effect(vfx.FadeOut(0.3))

    writer = VideoWriter("output_multi_text.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, title, subtitle, caption])
    writer.write()

    video.close()
    print("Created output_multi_text.mp4\n")


def example_lower_third():
    """Create a lower third text overlay."""
    print("Example 8: Lower third")

    video = VideoClip("input.mp4")

    # Background bar
    bar = ImageClip.from_color(
        color=(0, 0, 0, 200),  # Semi-transparent black
        size=(video.size[0], 120),
        duration=5
    )
    bar.set_position((0, video.size[1] - 120))
    bar.add_effect(vfx.FadeIn(0.5))
    bar.add_effect(vfx.FadeOut(0.5))

    # Name text
    canvas_name = Canvas().font_size(50).color("white").background_color("transparent")
    name = TextClip("John Doe", start=0, duration=5, canvas=canvas_name)
    name.set_position((40, video.size[1] - 100))
    name.add_effect(vfx.FadeIn(0.5))
    name.add_effect(vfx.FadeOut(0.5))

    # Title text
    canvas_title = Canvas().font_size(30).color("#AAAAAA").background_color("transparent")
    job_title = TextClip("Software Engineer", start=0, duration=5, canvas=canvas_title)
    job_title.set_position((40, video.size[1] - 50))
    job_title.add_effect(vfx.FadeIn(0.5))
    job_title.add_effect(vfx.FadeOut(0.5))

    writer = VideoWriter("output_lower_third.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, bar, name, job_title])
    writer.write()

    video.close()
    print("Created output_lower_third.mp4\n")


if __name__ == "__main__":
    print("=== Text Animation Examples ===\n")

    # Uncomment the examples you want to run
    example_simple_text()
    example_styled_text()
    example_fade_text()
    example_animated_position()
    example_bouncing_text()
    example_scaling_text()
    example_multiple_text_layers()
    example_lower_third()

    print("Done!")
