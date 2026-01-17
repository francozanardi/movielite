"""
Example: Using the speed feature in movielite

This example demonstrates how to use the set_speed() method to control
playback speed for video and audio clips.
"""

from movielite import VideoClip, AudioClip, ImageClip, VideoWriter

def example_basic_speed():
    """Basic example of speed control."""
    
    # Load a video clip
    video = VideoClip("input.mp4", start=0, duration=10)
    
    # Speed up the video to 2x (plays twice as fast)
    video.set_speed(2.0)
    
    # The video will now play in 5 seconds instead of 10
    # Both video frames and audio will be sped up
    
    writer = VideoWriter("output_2x_speed.mp4", fps=video.fps/2)
    writer.add_clip(video)
    writer.write()
    
    video.close()


def example_slow_motion():
    """Create a slow motion effect."""
    
    video = VideoClip("action.mp4", start=0, duration=5)
    
    # Slow down to half speed (0.5x)
    video.set_speed(0.5)
    
    # The 5-second clip will now take 10 seconds to play
    # This creates a slow-motion effect
    
    writer = VideoWriter("slow_motion.mp4", fps=video.fps)
    writer.add_clip(video)
    writer.write()
    
    video.close()


def example_mixed_speeds():
    """Combine clips with different speeds."""
    
    # Normal speed intro
    intro = VideoClip("intro.mp4", start=0, duration=3)
    intro.set_speed(1.0)  # Normal speed
    
    # Fast action sequence
    action = VideoClip("action.mp4", start=intro.end, duration=10)
    action.set_speed(2.0)  # 2x speed - will play in 5 seconds
    
    # Slow motion highlight
    highlight = VideoClip("highlight.mp4", start=action.end, duration=5)
    highlight.set_speed(0.5)  # 0.5x speed - will play in 10 seconds
    
    # Normal speed outro
    outro = VideoClip("outro.mp4", start=highlight.end, duration=3)
    outro.set_speed(1.0)
    
    writer = VideoWriter("final.mp4", fps=30)
    writer.add_clips([intro, action, highlight, outro])
    writer.write()
    
    for clip in [intro, action, highlight, outro]:
        clip.close()


def example_audio_speed():
    """Control audio speed independently."""
    
    video = VideoClip("video.mp4", start=0, duration=10)
    
    # Speed up video to 2x
    video.set_speed(2.0)
    
    # The video's audio is automatically sped up too
    # But you can also control audio independently:
    
    # Option 1: Use a separate audio track at normal speed
    music = AudioClip("background.mp3", start=0, duration=10)
    music.set_speed(1.0)  # Keep music at normal speed
    
    writer = VideoWriter("output.mp4", fps=video.fps)
    writer.add_clip(video)
    writer.add_clip(music)
    writer.write()
    
    video.close()


def example_time_remapping():
    """Advanced: Create a time-remapping effect."""
    
    # Create segments with different speeds for a dynamic effect
    video_path = "input.mp4"
    
    # Segment 1: Normal speed (0-2s)
    seg1 = VideoClip(video_path, start=0, duration=2, offset=0)
    seg1.set_speed(1.0)
    
    # Segment 2: Fast forward (2-4s, covering 4s of source)
    seg2 = VideoClip(video_path, start=2, duration=4, offset=2)
    seg2.set_speed(2.0)
    
    # Segment 3: Slow motion (4-8s, covering 2s of source)
    seg3 = VideoClip(video_path, start=4, duration=2, offset=6)
    seg3.set_speed(0.5)
    
    # Segment 4: Very fast (8-9s, covering 4s of source)
    seg4 = VideoClip(video_path, start=8, duration=4, offset=8)
    seg4.set_speed(4.0)
    
    writer = VideoWriter("time_remap.mp4", fps=30)
    writer.add_clips([seg1, seg2, seg3, seg4])
    writer.write()
    
    for clip in [seg1, seg2, seg3, seg4]:
        clip.close()


if __name__ == "__main__":
    print("Speed Feature Examples")
    print("=" * 50)
    print("\nAvailable examples:")
    print("1. example_basic_speed() - Basic 2x speed")
    print("2. example_slow_motion() - Slow motion effect")
    print("3. example_mixed_speeds() - Multiple clips with different speeds")
    print("4. example_audio_speed() - Independent audio speed control")
    print("5. example_time_remapping() - Advanced time remapping")
    print("\nNote: These examples require actual video files to run.")
    print("Modify the file paths to match your video files.")
    example_chaining()
