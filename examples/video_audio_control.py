"""
Example: Controlling video audio track.

This example demonstrates how to access and modify the audio track of a video clip.
"""
import sys
sys.path.insert(0, 'src')

from movielite import VideoClip, AudioClip, VideoWriter, afx

# Example 1: Modify video audio independently
print("Example 1: Fade in/out on video audio")
video = VideoClip("sample.mp4", start=0, duration=10)

# Access and modify the audio track
video.audio.add_effect(afx.FadeIn(2.0)).add_effect(afx.FadeOut(2.0)).set_volume(0.7)

writer = VideoWriter("output_with_faded_audio.mp4", duration=10)
writer.add_clip(video)
writer.write()

# Example 2: Move audio independently from video
print("\nExample 2: Offset audio from video")
video2 = VideoClip("sample.mp4", start=0, duration=10)

# Video starts at 0, but audio starts at 2 seconds
video2.audio._start = 2.0

writer2 = VideoWriter("output_audio_delayed.mp4", duration=12)
writer2.add_clip(video2)
writer.write()

# Example 3: Combine video with separate background music
print("\nExample 3: Video with background music")
video3 = VideoClip("sample.mp4", start=0, duration=10)

# Reduce video audio volume
video3.audio.set_volume(0.3)

# Add background music
music = AudioClip("music.mp3", start=0, duration=10)
music.set_volume(0.7)

writer3 = VideoWriter("output_with_music.mp4", duration=10)
writer3.add_clip(video3)
writer3.add_clip(music)
writer3.write()

# Example 4: Modify video timing and audio stays synced
print("\nExample 4: Video timing changes sync to audio")
video4 = VideoClip("sample.mp4", start=0, duration=10)

# Both video and audio start at 5 seconds
video4.set_start(5.0)

# Both video and audio are 8 seconds long
video4.set_duration(8.0)

writer4 = VideoWriter("output_synced.mp4", duration=15)
writer4.add_clip(video4)
writer4.write()

print("\nAll examples completed!")
print("\nKey features:")
print("- video.audio: Access audio track")
print("- video.audio.fade_in/fade_out/set_volume: Apply audio effects")
print("- video.audio._start: Move audio independently")
print("- video.set_start/set_duration: Automatically syncs audio")
