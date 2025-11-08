"""
Showcase of all built-in visual and audio effects in movielite.

Demonstrates the full effect library with practical examples.
"""

from movielite import VideoClip, AudioClip, VideoWriter, vfx, afx, VideoQuality


def example_fade_effects():
    """Demonstrate fade in and fade out effects."""
    print("Example 1: Fade effects")

    clip = VideoClip("input.mp4")
    clip.add_effect(vfx.FadeIn(duration=2.0))
    clip.add_effect(vfx.FadeOut(duration=1.5))

    writer = VideoWriter("output_fade.mp4", fps=clip.fps, size=clip.size)
    writer.add_clip(clip)
    writer.write()

    clip.close()
    print("Created output_fade.mp4\n")


def example_blur_effects():
    """Demonstrate blur, blur-in, and blur-out effects."""
    print("Example 2: Blur effects")

    # Static blur
    clip1 = VideoClip("input.mp4")
    clip1.add_effect(vfx.Blur(intensity=7.0))

    writer = VideoWriter("output_blur.mp4", fps=clip1.fps, size=clip1.size)
    writer.add_clip(clip1)
    writer.write()
    clip1.close()

    # Blur in (starts blurred, becomes clear)
    clip2 = VideoClip("input.mp4")
    clip2.add_effect(vfx.BlurIn(duration=3.0, max_intensity=15.0))

    writer = VideoWriter("output_blur_in.mp4", fps=clip2.fps, size=clip2.size)
    writer.add_clip(clip2)
    writer.write()
    clip2.close()

    # Blur out (starts clear, becomes blurred)
    clip3 = VideoClip("input.mp4")
    clip3.add_effect(vfx.BlurOut(duration=3.0, max_intensity=15.0))

    writer = VideoWriter("output_blur_out.mp4", fps=clip3.fps, size=clip3.size)
    writer.add_clip(clip3)
    writer.write()
    clip3.close()

    print("Created blur effect videos\n")


def example_color_effects():
    """Demonstrate color adjustment effects."""
    print("Example 3: Color effects")

    # Increase saturation
    clip1 = VideoClip("input.mp4")
    clip1.add_effect(vfx.Saturation(factor=1.5))

    writer = VideoWriter("output_saturated.mp4", fps=clip1.fps, size=clip1.size)
    writer.add_clip(clip1)
    writer.write()
    clip1.close()

    # Increase brightness
    clip2 = VideoClip("input.mp4")
    clip2.add_effect(vfx.Brightness(factor=1.3))

    writer = VideoWriter("output_bright.mp4", fps=clip2.fps, size=clip2.size)
    writer.add_clip(clip2)
    writer.write()
    clip2.close()

    # Increase contrast
    clip3 = VideoClip("input.mp4")
    clip3.add_effect(vfx.Contrast(factor=1.4))

    writer = VideoWriter("output_contrast.mp4", fps=clip3.fps, size=clip3.size)
    writer.add_clip(clip3)
    writer.write()
    clip3.close()

    # Black and white
    clip4 = VideoClip("input.mp4")
    clip4.add_effect(vfx.BlackAndWhite())

    writer = VideoWriter("output_bw.mp4", fps=clip4.fps, size=clip4.size)
    writer.add_clip(clip4)
    writer.write()
    clip4.close()

    # Sepia tone
    clip5 = VideoClip("input.mp4")
    clip5.add_effect(vfx.Sepia(intensity=1.0))

    writer = VideoWriter("output_sepia.mp4", fps=clip5.fps, size=clip5.size)
    writer.add_clip(clip5)
    writer.write()
    clip5.close()

    print("Created color effect videos\n")


def example_zoom_effects():
    """Demonstrate zoom and Ken Burns effects."""
    print("Example 4: Zoom effects")

    # Zoom in
    clip1 = VideoClip("input.mp4")
    clip1.add_effect(vfx.ZoomIn(duration=5.0, from_scale=0.5, to_scale=1.0))

    writer = VideoWriter("output_zoom_in.mp4", fps=clip1.fps, size=clip1.size)
    writer.add_clip(clip1)
    writer.write()
    clip1.close()

    # Zoom out
    clip2 = VideoClip("input.mp4")
    clip2.add_effect(vfx.ZoomOut(duration=5.0, from_scale=1.0, to_scale=0.7))

    writer = VideoWriter("output_zoom_out.mp4", fps=clip2.fps, size=clip2.size)
    writer.add_clip(clip2)
    writer.write()
    clip2.close()

    # Ken Burns effect (zoom + pan)
    clip3 = VideoClip("input.mp4")
    clip3.add_effect(vfx.KenBurns(
        start_scale=1.0,
        end_scale=1.3,
        start_position=(0, 0),
        end_position=(-100, -50)
    ))

    writer = VideoWriter("output_ken_burns.mp4", fps=clip3.fps, size=clip3.size)
    writer.add_clip(clip3)
    writer.write()
    clip3.close()

    print("Created zoom effect videos\n")


def example_glitch_effects():
    """Demonstrate glitch and distortion effects."""
    print("Example 5: Glitch effects")

    # Digital glitch
    clip1 = VideoClip("input.mp4")
    clip1.add_effect(vfx.Glitch(
        intensity=0.7,
        rgb_shift=True,
        horizontal_lines=True,
        scan_lines=True
    ))

    writer = VideoWriter("output_glitch.mp4", fps=clip1.fps, size=clip1.size)
    writer.add_clip(clip1)
    writer.write()
    clip1.close()

    # Chromatic aberration
    clip2 = VideoClip("input.mp4")
    clip2.add_effect(vfx.ChromaticAberration(intensity=8.0))

    writer = VideoWriter("output_chromatic.mp4", fps=clip2.fps, size=clip2.size)
    writer.add_clip(clip2)
    writer.write()
    clip2.close()

    # Pixelate
    clip3 = VideoClip("input.mp4")
    clip3.add_effect(vfx.Pixelate(block_size=15))

    writer = VideoWriter("output_pixelate.mp4", fps=clip3.fps, size=clip3.size)
    writer.add_clip(clip3)
    writer.write()
    clip3.close()

    print("Created glitch effect videos\n")


def example_vignette_effect():
    """Demonstrate vignette effect."""
    print("Example 6: Vignette effect")

    clip = VideoClip("input.mp4")
    clip.add_effect(vfx.Vignette(intensity=0.6, radius=0.7))

    writer = VideoWriter("output_vignette.mp4", fps=clip.fps, size=clip.size)
    writer.add_clip(clip)
    writer.write()

    clip.close()
    print("Created output_vignette.mp4\n")


def example_combined_effects():
    """Demonstrate combining multiple effects."""
    print("Example 7: Combined effects")

    clip = VideoClip("input.mp4")

    # Apply multiple effects in sequence
    clip.add_effect(vfx.FadeIn(1.0))
    clip.add_effect(vfx.Saturation(1.3))
    clip.add_effect(vfx.Contrast(1.2))
    clip.add_effect(vfx.Vignette(intensity=0.4, radius=0.8))
    clip.add_effect(vfx.FadeOut(1.5))

    writer = VideoWriter("output_combined.mp4", fps=clip.fps, size=clip.size)
    writer.add_clip(clip)
    writer.write()

    clip.close()
    print("Created output_combined.mp4\n")


def example_audio_effects():
    """Demonstrate audio fade effects."""
    print("Example 8: Audio effects")

    video = VideoClip("input.mp4")

    # Apply fade to video's audio
    video.audio.add_effect(afx.FadeIn(2.0))
    video.audio.add_effect(afx.FadeOut(2.0))

    # Add background music with fade
    music = AudioClip("background.mp3", start=0, volume=0.3)
    music.add_effect(afx.FadeIn(3.0))
    music.add_effect(afx.FadeOut(3.0))

    writer = VideoWriter("output_audio_effects.mp4", fps=video.fps, size=video.size)
    writer.add_clip(video)
    writer.add_clip(music)
    writer.write()

    video.close()
    print("Created output_audio_effects.mp4\n")


if __name__ == "__main__":
    print("=== Visual and Audio Effects Showcase ===\n")

    # Uncomment the examples you want to run
    # example_fade_effects()
    # example_blur_effects()
    # example_color_effects()
    # example_zoom_effects()
    # example_glitch_effects()
    # example_vignette_effect()
    # example_combined_effects()
    # example_audio_effects()

    print("Done!")
