from .base import VideoReader
from .cv2_reader import Cv2Reader
from .ffmpeg_reader import FfmpegReader
from ...logger import get_logger


def open_reader(path: str, *, with_alpha: bool = False) -> VideoReader:
    """Open a video for reading, picking the fastest backend that can decode it.

    with_alpha=True forces FfmpegReader with pix_fmt=bgra: cv2 doesn't reliably
    handle alpha in video, and this is the path AlphaVideoClip takes.

    with_alpha=False (default) tries Cv2Reader first because it's roughly 10x
    faster than ffmpeg for sequential reads and uses ~30x less RAM. If cv2
    can't decode the codec (AV1, HEVC on stripped OpenCV builds, ...),
    probe() returns False and we fall back to FfmpegReader.

    The probe consumes the first frame; Cv2Reader caches it internally so
    the fallback path doesn't waste that decode.
    """
    if with_alpha:
        return FfmpegReader(path, pix_fmt="bgra")

    try:
        reader = Cv2Reader(path)
    except RuntimeError as e:
        get_logger().debug(f"Cv2Reader init failed for {path}: {e}. Falling back to ffmpeg.")
        return FfmpegReader(path, pix_fmt="bgr24")

    if reader.probe():
        return reader

    get_logger().info(f"cv2 could not decode {path}; falling back to ffmpeg.")
    reader.close()
    return FfmpegReader(path, pix_fmt="bgr24")
