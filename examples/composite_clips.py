"""
Composite clips examples using movielite.

Demonstrates when and how to use CompositeClip and AlphaCompositeClip.
Remember: These should only be used when you need to treat multiple clips as a single unit.
For most compositing tasks, use VideoWriter.add_clips() directly for better performance.
"""

from movielite import ImageClip, TextClip, VideoClip, VideoWriter, CompositeClip, AlphaCompositeClip


def example_composite_as_group():
    """
    Use CompositeClip to group elements and apply transformations to all at once.
    """
    print("Example 1: Group logo and text to transform together")

    # Create a logo with text
    logo = ImageClip("logo.png", start=0, duration=5)
    logo.set_position((0, 0))
    logo.set_size(100, 100)

    text = TextClip("My Brand", start=0, duration=5)
    text.set_position((logo.size[1] + 20, 50))

    # Combine them into a composite
    branding = CompositeClip(
        clips=[logo, text],
        start=0,  # Starts at t=0s in the final video
        size=(300, 200)
        # duration auto-calculated as max(0+5, 0+5) = 5 seconds
    )

    # Now we can transform the entire branding unit
    branding.set_position((50, 50))  # Position the entire group
    branding.set_scale(0.8)  # Scale everything together
    branding.set_opacity(0.9)  # Apply opacity to the whole group

    # Add to video
    video = VideoClip("video.mp4")

    writer = VideoWriter("output_branding.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, branding])
    writer.write()

    video.close()
    print("Created output_branding.mp4\n")


def example_reusable_composite():
    """
    Create a reusable composite element that appears multiple times.
    """
    print("Example 2: Reusable composite element")

    def create_caption(text: str, start: float) -> CompositeClip:
        """Create a caption with background."""
        bg = ImageClip.from_color((0, 0, 0), (400, 100), start=0, duration=3)
        bg.set_opacity(0.7)

        caption = TextClip(text, start=0, duration=3)
        caption.set_position((20, 30))

        composite = CompositeClip(
            clips=[bg, caption],
            start=start,
            size=(400, 100)
            # duration auto-calculated as 3 seconds
        )
        composite.set_position((100, 500))

        return composite

    # Create multiple instances
    caption1 = create_caption("Scene 1", start=0)
    caption2 = create_caption("Scene 2", start=5)
    caption3 = create_caption("Scene 3", start=10)

    video = VideoClip("video.mp4")

    writer = VideoWriter("output_captions.mp4", fps=video.fps, size=video.size)
    writer.add_clip(video)
    writer.add_clips([caption1, caption2, caption3])
    writer.write()

    video.close()
    print("Created output_captions.mp4\n")


def example_alpha_composite_transparency():
    """
    Use AlphaCompositeClip when you need transparency in the composite output.
    """
    print("Example 3: Transparent watermark with alpha composite")

    # Create transparent background
    bg = ImageClip.from_color((255, 255, 255, 0), (300, 150), start=0, duration=10)

    # Add logo with transparency
    logo = ImageClip("logo_with_alpha.png", start=0, duration=10)
    logo.set_position((10, 10))
    logo.set_opacity(0.6)

    # Add text
    text = TextClip("© 2024", start=0, duration=10)
    text.set_position((10, 100))
    text.set_opacity(0.5)

    # Use AlphaCompositeClip to preserve transparency
    watermark = AlphaCompositeClip(
        clips=[bg, logo, text],
        start=0,
        size=(300, 150)
        # duration auto-calculated as 10 seconds
    )
    watermark.set_position((200, 300))

    video = VideoClip("video.mp4")

    writer = VideoWriter("output_watermark.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, watermark])
    writer.write()

    video.close()
    print("Created output_watermark.mp4\n")


def example_animated_composite():
    """
    Composite with internal timing - elements appear at different times.
    """
    print("Example 4: Animated composite with relative timing")

    # Elements with different start times (relative to composite)
    title = TextClip("Welcome!", start=0, duration=3)
    title.set_position((100, 50))

    subtitle = TextClip("to our channel", start=1, duration=3)  # Appears 1s after title
    subtitle.set_position((120, 120))

    icon = ImageClip("logo.png", start=0.5, duration=3.5)  # Appears 0.5s after title
    icon.set_position((50, 60))
    icon.set_scale(0.5)

    # Combine with relative timings
    intro = AlphaCompositeClip(
        clips=[icon, title, subtitle],
        start=2,  # Entire animation starts at t=2s
        size=(400, 200)
        # duration auto-calculated as max(0+3, 1+3, 0.5+3.5) = 4 seconds
    )
    intro.set_position((760, 440))  # Centered on 1920x1080

    # So: title appears at t=2s, icon at t=2.5s, subtitle at t=3s

    video = VideoClip("video.mp4")

    writer = VideoWriter("output_intro.mp4", fps=video.fps, size=video.size)
    writer.add_clips([video, intro])
    writer.write()

    video.close()
    print("Created output_intro.mp4\n")


def example_when_not_to_use_composite():
    """
    COUNTER-EXAMPLE: Don't use CompositeClip when you just need to stack clips.

    This shows the WRONG and RIGHT way to do simple compositing.
    """
    print("Example 5: When NOT to use CompositeClip")

    # WRONG: Using CompositeClip for simple stacking (less performant)
    print("  ❌ Wrong approach (using CompositeClip unnecessarily):")

    bg = VideoClip("video.mp4", start=0)
    overlay = ImageClip("logo.png", start=2, duration=5)
    overlay.set_position((100, 100))

    # Don't do this:
    # composite = CompositeClip(clips=[bg, overlay], start=0, size=bg.size)
    # writer.add_clip(composite)

    # RIGHT: Use VideoWriter.add_clips() directly (more performant)
    print("  ✓ Correct approach (using add_clips directly):")

    writer = VideoWriter("output_simple.mp4", fps=bg.fps, size=bg.size)
    writer.add_clips([bg, overlay])  # Much better!
    writer.write()

    bg.close()
    print("Created output_simple.mp4\n")
    print("  Use CompositeClip only when you need to transform clips as a group!")


if __name__ == "__main__":
    print("=== Composite Clips Examples ===\n")
    print("Note: CompositeClip/AlphaCompositeClip should only be used when necessary.")
    print("For simple compositing, use VideoWriter.add_clips() instead.\n")

    # Uncomment the examples you want to run
    # example_composite_as_group()
    # example_reusable_composite()
    # example_alpha_composite_transparency()
    # example_animated_composite()
    # example_when_not_to_use_composite()

    print("Done!")
