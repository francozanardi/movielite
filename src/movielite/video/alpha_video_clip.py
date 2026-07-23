from .video_clip import VideoClip
from .readers import VideoReader, open_reader


class AlphaVideoClip(VideoClip):
    """
    A video clip that loads and processes frames in BGRA format (with alpha channel).

    This class supports video transparency but has a performance penalty compared to VideoClip
    (~33% more memory per frame due to the additional alpha channel). Only use this when you need
    transparency support.
    """

    def _open_reader(self, path: str) -> VideoReader:
        return open_reader(path, with_alpha=True)
