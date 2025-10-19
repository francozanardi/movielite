"""
Basic usage example of movielite
"""

from movielite import VideoClip, ImageClip, TextClip, AudioClip, VideoWriter, concatenate_videoclips
from movielite.fx import fade_in, fade_out, resize

def example_1_simple_overlay():
    """Add a text overlay to a video"""
    # Load background video
    bg = VideoClip("input.mp4")

    # Add text overlay
    text = TextClip("Hello World!", start=2, duration=3)
    text.set_position((100, 100))
    fade_in(text, duration=0.5)

    # Write to file
    writer = VideoWriter("output_with_text.mp4", fps=bg.fps, size=bg.size)
    writer.add_clip(bg)
    writer.add_clip(text)
    writer.write(use_multiprocessing=False)

def example_images():
    """Add a text overlay to a video"""
    # Load background video
    scene_0 = ImageClip("scene_0_image.png", duration=5.0)
    scene_1 = ImageClip("scene_1_image.png", start=5, duration=5.0)
    scene_2 = ImageClip("scene_2_image.png", start=10, duration=5.0)

    # Add text overlay
    text = TextClip("Hello World!", start=2, duration=3)
    text.set_position((100, 100))
    fade_in(text, duration=0.5)

    # Write to file
    writer = VideoWriter("output_images.mp4", fps=24, size=(1920, 1080))
    writer.add_clip(scene_0)
    writer.add_clip(scene_1)
    writer.add_clip(scene_2)
    writer.add_clip(text)
    writer.write(use_multiprocessing=False)


def example_2_concatenate_videos():
    """Concatenate multiple videos"""
    clip1 = VideoClip("intro.mp4")
    clip2 = VideoClip("main.mp4")
    clip3 = VideoClip("outro.mp4")

    # Concatenate
    final = concatenate_videoclips([clip1, clip2, clip3])

    # Render the composite
    writer = VideoWriter("output_concatenated.mp4", fps=clip1.fps, size=clip1.size)
    writer.add_clip(final)
    writer.write()


def example_3_extract_and_resize():
    """Extract a segment and resize"""
    # Load video
    clip = VideoClip("video.mp4")

    # Extract 10 seconds starting at 5 seconds
    segment = clip.subclip(5, 15)

    # Resize to 720p width
    resize(segment, width=1280)

    # Render
    writer = VideoWriter("output.mp4", fps=segment.fps, size=segment.size)
    writer.add_clip(segment)
    writer.write()


def example_4_audio_overlay():
    """Add background music to video"""
    bg = VideoClip("video.mp4")

    writer = VideoWriter("output_with_music.mp4", fps=bg.fps, size=bg.size)
    writer.add_clip(bg)

    # Add background music at 50% volume
    music = AudioClip("music.mp3", start=0, volume=0.5)
    writer.add_audio(music)

    # Add sound effect at 5 seconds
    sfx = AudioClip("ding.wav", start=5, volume=1.0)
    writer.add_audio(sfx)

    writer.write()


def example_5_custom_transformation():
    """Apply custom frame transformation"""
    import cv2

    bg = VideoClip("video.mp4")

    # Create an image clip
    img = ImageClip("overlay.png", start=1, duration=5)

    # Apply custom transformation
    def make_sepia(frame, t):
        # Simple sepia tone effect
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        sepia = cv2.merge([gray * 0.7, gray * 0.9, gray])
        return sepia

    img.transform_frame(make_sepia)
    img.set_position((50, 50))

    writer = VideoWriter("output_sepia.mp4", fps=bg.fps, size=bg.size)
    writer.add_clip(bg)
    writer.add_clip(img)
    writer.write()


if __name__ == "__main__":
    print("movielite examples")
    print("Uncomment the example you want to run")

    example_images()
    # example_1_simple_overlay()
    # example_2_concatenate_videos()
    # example_3_extract_and_resize()
    # example_4_audio_overlay()
    # example_5_custom_transformation()
