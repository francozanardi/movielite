"""
Transition examples using movielite.

Demonstrates various transition effects between clips.
"""

from movielite import VideoClip, VideoWriter, VideoQuality, vtx


def example_crossfade():
    """Simple crossfade transition between two clips."""
    print("Example 1: Crossfade transition")

    # Clips must overlap for transition
    clip1 = VideoClip("scene1.mp4", start=0, duration=5)
    clip2 = VideoClip("scene2.mp4", start=4.5, duration=5)  # 0.5s overlap

    # Apply crossfade during overlap
    clip1.add_transition(clip2, vtx.CrossFade(duration=0.5))

    total_duration = clip1.duration + clip2.duration - 0.5  # Account for overlap

    writer = VideoWriter("output_crossfade.mp4", fps=30, size=clip1.size, duration=total_duration)
    writer.add_clips([clip1, clip2])
    writer.write()

    clip1.close()
    clip2.close()
    print("Created output_crossfade.mp4\n")


def example_blur_dissolve():
    """Blur dissolve transition (blurs during transition)."""
    print("Example 2: Blur dissolve transition")

    clip1 = VideoClip("scene1.mp4", start=0, duration=5)
    clip2 = VideoClip("scene2.mp4", start=4.0, duration=5)  # 1.0s overlap

    # Apply blur dissolve
    clip1.add_transition(clip2, vtx.BlurDissolve(duration=1.0, max_blur=15.0))

    total_duration = clip1.duration + clip2.duration - 1.0

    writer = VideoWriter("output_blur_dissolve.mp4", fps=30, size=clip1.size, duration=total_duration)
    writer.add_clips([clip1, clip2])
    writer.write()

    clip1.close()
    clip2.close()
    print("Created output_blur_dissolve.mp4\n")


def example_multiple_transitions():
    """Multiple clips with transitions between each."""
    print("Example 3: Multiple transitions")

    # Create 3 clips with overlaps
    clip1 = VideoClip("scene1.mp4", start=0, duration=4)
    clip2 = VideoClip("scene2.mp4", start=3.5, duration=4)  # 0.5s overlap
    clip3 = VideoClip("scene3.mp4", start=7.0, duration=4)  # 0.5s overlap with clip2

    # Apply different transitions
    clip1.add_transition(clip2, vtx.CrossFade(duration=0.5))
    clip2.add_transition(clip3, vtx.Dissolve(duration=0.5))

    total_duration = 11.0  # 4 + 4 + 4 - 0.5 - 0.5

    writer = VideoWriter("output_multi_transitions.mp4", fps=30, size=clip1.size, duration=total_duration)
    writer.add_clips([clip1, clip2, clip3])
    writer.write()

    clip1.close()
    clip2.close()
    clip3.close()
    print("Created output_multi_transitions.mp4\n")


def example_long_crossfade():
    """Longer crossfade for smoother transition."""
    print("Example 4: Long crossfade")

    clip1 = VideoClip("scene1.mp4", start=0, duration=8)
    clip2 = VideoClip("scene2.mp4", start=6.0, duration=8)  # 2.0s overlap

    # Longer crossfade creates smoother transition
    clip1.add_transition(clip2, vtx.CrossFade(duration=2.0))

    total_duration = clip1.duration + clip2.duration - 2.0

    writer = VideoWriter("output_long_crossfade.mp4", fps=30, size=clip1.size, duration=total_duration)
    writer.add_clips([clip1, clip2])
    writer.write()

    clip1.close()
    clip2.close()
    print("Created output_long_crossfade.mp4\n")


def example_transition_with_effects():
    """Combine transitions with other effects."""
    print("Example 5: Transition with effects")

    from movielite import vfx

    clip1 = VideoClip("scene1.mp4", start=0, duration=5)
    clip2 = VideoClip("scene2.mp4", start=4.5, duration=5)

    # Add effects to individual clips
    clip1.add_effect(vfx.Saturation(1.3))
    clip2.add_effect(vfx.Brightness(1.1))

    # Add transition between them
    clip1.add_transition(clip2, vtx.CrossFade(duration=0.5))

    total_duration = clip1.duration + clip2.duration - 0.5

    writer = VideoWriter("output_transition_effects.mp4", fps=30, size=clip1.size, duration=total_duration)
    writer.add_clips([clip1, clip2])
    writer.write()

    clip1.close()
    clip2.close()
    print("Created output_transition_effects.mp4\n")


def example_slideshow():
    """Create a slideshow with transitions."""
    print("Example 6: Slideshow with transitions")

    from movielite import ImageClip

    # Create image clips
    images = [
        ImageClip("photo1.jpg", start=0, duration=3),
        ImageClip("photo2.jpg", start=2.5, duration=3),     # 0.5s overlap
        ImageClip("photo3.jpg", start=5.0, duration=3),     # 0.5s overlap
        ImageClip("photo4.jpg", start=7.5, duration=3),     # 0.5s overlap
    ]

    # Apply crossfade between each
    for i in range(len(images) - 1):
        images[i].add_transition(images[i + 1], vtx.CrossFade(duration=0.5))

    total_duration = 9.5  # 3 + 3 + 3 + 3 - 0.5 - 0.5 - 0.5

    writer = VideoWriter("output_slideshow.mp4", fps=30, size=images[0].size, duration=total_duration)
    writer.add_clips(images)
    writer.write()

    print("Created output_slideshow.mp4\n")


if __name__ == "__main__":
    print("=== Transition Examples ===\n")

    # Uncomment the examples you want to run
    example_crossfade()
    example_blur_dissolve()
    # example_multiple_transitions()
    # example_long_crossfade()
    # example_transition_with_effects()
    # example_slideshow()

    print("Done!")
