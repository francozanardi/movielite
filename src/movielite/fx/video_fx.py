from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.clip import Clip

def fade_in(clip: 'Clip', duration: float = 1.0) -> 'Clip':
    """
    Apply a fade-in effect to a clip.

    Args:
        clip: The clip to apply fade-in to
        duration: Duration of the fade-in effect in seconds

    Returns:
        The clip with fade-in applied (for chaining)

    Example:
        >>> from movielite.fx import fade_in
        >>> clip = VideoClip("video.mp4")
        >>> fade_in(clip, duration=2.0)
    """
    original_opacity = clip._opacity

    def opacity_with_fade(t):
        base_opacity = original_opacity(t)
        if t < duration:
            return base_opacity * (t / duration)
        return base_opacity

    clip._opacity = opacity_with_fade
    return clip


def fade_out(clip: 'Clip', duration: float = 1.0) -> 'Clip':
    """
    Apply a fade-out effect to a clip.

    Args:
        clip: The clip to apply fade-out to
        duration: Duration of the fade-out effect in seconds

    Returns:
        The clip with fade-out applied (for chaining)

    Example:
        >>> from movielite.fx import fade_out
        >>> clip = VideoClip("video.mp4")
        >>> fade_out(clip, duration=2.0)
    """
    original_opacity = clip._opacity
    clip_duration = clip._duration

    def opacity_with_fade(t):
        base_opacity = original_opacity(t)
        time_from_end = clip_duration - t
        if time_from_end < duration:
            return base_opacity * (time_from_end / duration)
        return base_opacity

    clip._opacity = opacity_with_fade
    return clip


def resize(clip: 'Clip', width: int = None, height: int = None) -> 'Clip':
    """
    Resize a clip to the specified dimensions.

    Args:
        clip: The clip to resize
        width: Target width (optional, maintains aspect ratio if height is provided)
        height: Target height (optional, maintains aspect ratio if width is provided)

    Returns:
        The clip with new size (for chaining)

    Example:
        >>> from movielite.fx import resize
        >>> clip = VideoClip("video.mp4")
        >>> resize(clip, width=1280)
    """
    clip.set_size(width=width, height=height)
    return clip
