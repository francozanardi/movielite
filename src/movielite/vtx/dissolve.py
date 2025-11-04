from .crossfade import CrossFade

# Dissolve is just an alias for CrossFade
class Dissolve(CrossFade):
    """
    Dissolve transition (alias for CrossFade).

    Smoothly blends from one clip to another by fading out the first clip
    while fading in the second clip over the specified duration.
    Applies to both video and audio (if the clips are VideoClips with audio).
    This requires the clips to have overlapping time ranges.
    """
    pass
