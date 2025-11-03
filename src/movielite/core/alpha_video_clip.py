from .video_clip import VideoClip
from .logger import get_logger
import numpy as np
import subprocess
from typing import Optional

class AlphaVideoClip(VideoClip):
    """
    A video clip that loads and processes frames in BGRA format (with alpha channel).

    This class supports video transparency but has a performance penalty compared to VideoClip
    (~33% more memory per frame due to the alpha channel). Only use this when you need
    transparency support.
    """

    def __init__(self, path: str, start: float = 0, duration: Optional[float] = None, offset: float = 0):
        """
        Load a video clip with alpha channel support.

        Args:
            path: Path to the video file
            start: Start time in the composition (seconds)
            duration: Duration to use from the video (if None, uses full video duration)
            offset: Start offset within the video file (seconds)
        """
        super().__init__(path, start, duration, offset)
        self._ffmpeg_proc = None

    def _load_metadata(self, path: str) -> None:
        """Load video metadata using FFprobe"""
        cmd = [
            "ffprobe",
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,r_frame_rate,duration',
            '-of', 'csv=p=0',
            path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parts = result.stdout.strip().split(',')

        w = int(parts[0])
        h = int(parts[1])

        # Parse frame rate (could be "30/1" or "30000/1001")
        fps_parts = parts[2].split('/')
        self._fps = float(fps_parts[0]) / float(fps_parts[1])

        # Get duration if available
        duration = None
        if len(parts) > 3 and parts[3] and parts[3] != 'N/A':
            duration = float(parts[3])

        # Count frames accurately using -count_frames (slower but accurate)
        cmd_count = [
            "ffprobe",
            '-v', 'error',
            '-select_streams', 'v:0',
            '-count_frames',
            '-show_entries', 'stream=nb_read_frames',
            '-of', 'csv=p=0',
            path
        ]

        result_count = subprocess.run(cmd_count, capture_output=True, text=True, check=True)
        frame_count_str = result_count.stdout.strip()

        # Parse frame count
        if frame_count_str and frame_count_str != 'N/A':
            self._total_frames = int(frame_count_str)
        elif duration is not None:
            # Fallback to duration * fps
            self._total_frames = int(duration * self._fps)
        else:
            raise RuntimeError(f"Could not determine frame count for video: {path}")

        if self._fps <= 0 or w <= 0 or h <= 0 or self._total_frames <= 0:
            raise RuntimeError(f"Invalid video properties for: {path}")

        self._size = (w, h)

        get_logger().debug(f"AlphaVideoClip loaded: {path}, size=({w}, {h}), fps={self._fps}, frames={self._total_frames}")

    def get_frame(self, t_rel: float) -> np.ndarray:
        """Get frame at relative time within this clip, in BGRA format"""
        actual_time = t_rel + self._offset
        target_frame_idx = int(actual_time * self._fps)
        target_frame_idx = max(0, min(target_frame_idx, self._total_frames - 1))

        if target_frame_idx == self._last_frame_idx and self._last_frame is not None:
            return self._last_frame

        needs_seeking = target_frame_idx < self._last_frame_idx or target_frame_idx - self._last_frame_idx > 10
        if self._ffmpeg_proc is None or needs_seeking:
            self._open_ffmpeg_at_frame(target_frame_idx)

        current_frame_idx = self._last_frame_idx
        while current_frame_idx < target_frame_idx:
            frame = self._read_next_frame()
            current_frame_idx += 1

        self._last_frame_idx = current_frame_idx
        self._last_frame = frame

        return frame

    def _open_ffmpeg_at_frame(self, start_frame: int):
        """Open FFmpeg pipe starting at specific frame"""
        if self._ffmpeg_proc is not None:
            self._close_ffmpeg()

        start_time = start_frame / self._fps

        cmd = [
            "ffmpeg",
            '-ss', str(start_time),  # Seek to position
            '-i', self._path,
            '-f', 'rawvideo',
            '-pix_fmt', 'bgra',
            '-vsync', '0',
            '-'
        ]

        self._ffmpeg_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**8
        )
        self._last_frame_idx = start_frame - 1

        get_logger().debug(f"AlphaVideoClip: Opened FFmpeg pipe at frame {start_frame} for {self._path}")

    def _read_next_frame(self) -> np.ndarray:
        """Read next frame from FFmpeg pipe"""
        if self._ffmpeg_proc is None:
            self._open_ffmpeg_at_frame(0)

        frame_size = self._size[0] * self._size[1] * 4  # BGRA = 4 bytes per pixel
        raw_frame = self._ffmpeg_proc.stdout.read(frame_size)

        if len(raw_frame) < frame_size:
            get_logger().warning(f"Failed to read frame from FFmpeg pipe for {self._path}")
            return np.zeros((self._size[1], self._size[0], 4), dtype=np.uint8)

        return np.frombuffer(raw_frame, dtype=np.uint8).reshape((self._size[1], self._size[0], 4))

    def _close_ffmpeg(self):
        """Close FFmpeg pipe"""
        if hasattr(self, '_ffmpeg_proc') and self._ffmpeg_proc is not None:
            self._ffmpeg_proc.stdout.close()
            self._ffmpeg_proc.terminate()
            self._ffmpeg_proc.wait()
            self._ffmpeg_proc = None

    def close(self):
        """Close the video file and FFmpeg pipe"""
        super().close()
        self._close_ffmpeg()

    def subclip(self, start: float, end: float) -> 'AlphaVideoClip':
        """
        Extract a subclip from this video.

        Args:
            start: Start time within this clip (seconds)
            end: End time within this clip (seconds)

        Returns:
            New AlphaVideoClip instance
        """
        new_clip: AlphaVideoClip = super().subclip(start, end)
        new_clip._ffmpeg_proc = None

        return new_clip
