from typing import List
from .video_clip import VideoClip
from .audio_clip import AudioClip
from .composite_clip import CompositeClip

def concatenate_videoclips(clips: List[VideoClip]) -> CompositeClip:
    """
    Concatenate multiple video clips sequentially.

    Args:
        clips: List of VideoClip instances to concatenate

    Returns:
        CompositeClip containing all clips played sequentially

    Example:
        >>> clip1 = VideoClip("video1.mp4")
        >>> clip2 = VideoClip("video2.mp4")
        >>> final = concatenate_videoclips([clip1, clip2])
    """
    if not clips:
        raise ValueError("Cannot concatenate empty list of clips")

    # Adjust start times for sequential playback
    current_time = 0
    adjusted_clips = []

    for clip in clips:
        # Create a new clip instance with adjusted start time
        new_clip = VideoClip.__new__(VideoClip)
        new_clip._frames = clip._frames
        new_clip._num_frames = clip._num_frames
        new_clip._fps = clip._fps
        new_clip._size = clip._size
        new_clip._offset = clip._offset
        new_clip._start = current_time
        new_clip._duration = clip._duration
        new_clip._position = clip._position
        new_clip._opacity = clip._opacity
        new_clip._scale = clip._scale
        new_clip._frame_transform = clip._frame_transform

        adjusted_clips.append(new_clip)
        current_time += clip._duration

    # Get the maximum size
    max_width = max(clip.size[0] for clip in clips)
    max_height = max(clip.size[1] for clip in clips)

    return CompositeClip(
        clips=adjusted_clips,
        start=0,
        duration=current_time,
        size=(max_width, max_height)
    )


def concatenate_audioclips(clips: List[AudioClip]) -> List[AudioClip]:
    """
    Concatenate multiple audio clips sequentially.

    Args:
        clips: List of AudioClip instances to concatenate

    Returns:
        List of AudioClip instances with adjusted start times

    Example:
        >>> audio1 = AudioClip("audio1.mp3")
        >>> audio2 = AudioClip("audio2.mp3")
        >>> concatenated = concatenate_audioclips([audio1, audio2])
    """
    if not clips:
        raise ValueError("Cannot concatenate empty list of clips")

    # Adjust start times for sequential playback
    current_time = 0
    adjusted_clips = []

    for clip in clips:
        new_clip = AudioClip(
            path=clip._path,
            start=current_time,
            duration=clip._duration,
            volume=clip._volume,
            offset=clip._offset
        )
        adjusted_clips.append(new_clip)
        current_time += clip._duration

    return adjusted_clips
