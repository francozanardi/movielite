"""
Basic video editing examples using movielite.

Demonstrates simple cuts, concatenation, and basic transformations.
"""

from movielite import VideoClip, VideoWriter


def example_extract_subclip():
    """Extract a 10-second segment from a video."""
    print("Example 1: Extract subclip")

    clip = VideoClip("input.mp4")
    segment = clip.subclip(5, 15)  # Extract seconds 5-15

    writer = VideoWriter("output_subclip.mp4", fps=clip.fps, size=clip.size)
    writer.add_clip(segment)
    writer.write()

    clip.close()
    print("Created output_subclip.mp4\n")


def example_concatenate_clips():
    """Concatenate multiple video clips sequentially."""
    print("Example 2: Concatenate clips")

    clip1 = VideoClip("intro.mp4", start=0)
    clip2 = VideoClip("main.mp4", start=clip1.duration)
    clip3 = VideoClip("outro.mp4", start=clip1.duration + clip2.duration)

    total_duration = clip1.duration + clip2.duration + clip3.duration

    writer = VideoWriter(
        "output_concat.mp4",
        fps=clip1.fps,
        size=clip1.size,
        duration=total_duration
    )
    writer.add_clips([clip1, clip2, clip3])
    writer.write()

    clip1.close()
    clip2.close()
    clip3.close()
    print("Created output_concat.mp4\n")


def example_resize_video():
    """Resize a video to 720p."""
    print("Example 3: Resize video")

    clip = VideoClip("input.mp4")
    clip.set_size(width=1280, height=720)

    writer = VideoWriter("output_720p.mp4", fps=clip.fps, size=(1280, 720))
    writer.add_clip(clip)
    writer.write()

    clip.close()
    print("Created output_720p.mp4\n")


def example_adjust_opacity():
    """Create a semi-transparent overlay effect."""
    print("Example 4: Adjust opacity")

    background = VideoClip("background.mp4", start=0)
    overlay = VideoClip("overlay.mp4", start=0)

    overlay.set_opacity(0.5)  # 50% transparent
    overlay.set_size(width=background.size[0], height=background.size[1])

    writer = VideoWriter("output_overlay.mp4", fps=background.fps, size=background.size)
    writer.add_clips([background, overlay])
    writer.write()

    background.close()
    overlay.close()
    print("Created output_overlay.mp4\n")


def example_position_clip():
    """Position a clip at a specific location."""
    print("Example 5: Position clip")

    background = VideoClip("background.mp4", start=0)
    small_clip = VideoClip("small.mp4", start=0)

    small_clip.set_size(width=320, height=180)
    small_clip.set_position((background.size[0] - 340, 20))  # Top-right corner

    writer = VideoWriter("output_positioned.mp4", fps=background.fps, size=background.size)
    writer.add_clips([background, small_clip])
    writer.write()

    background.close()
    small_clip.close()
    print("Created output_positioned.mp4\n")


def example_loop_video():
    """Loop a short video clip."""
    print("Example 7: Loop video")

    clip = VideoClip("short_clip.mp4", duration=10)  # 10 second duration
    clip.loop(True)  # Enable looping

    writer = VideoWriter("output_looped.mp4", fps=clip.fps, size=clip.size, duration=10)
    writer.add_clip(clip)
    writer.write()

    clip.close()
    print("Created output_looped.mp4\n")


if __name__ == "__main__":
    print("=== Basic Video Editing Examples ===\n")

    # Uncomment the examples you want to run
    # example_extract_subclip()
    # example_concatenate_clips()
    # example_resize_video()
    # example_adjust_opacity()
    # example_position_clip()
    # example_loop_video()

    print("Done!")
