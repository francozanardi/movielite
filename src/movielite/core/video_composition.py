import cv2
import numpy as np
import multiprocess as mp
import subprocess
import os
import tempfile
import math
import shutil
from typing import Tuple, List, Optional
from tqdm import tqdm
from .clip import Clip
from .audio_clip import AudioClip
from .enums import VideoQuality
from .logger import get_logger
from .utils import get_rotation

class VideoComposition:
    """
    Main composition class for rendering videos with clips and audio.

    This class handles:
    - Loading a base video
    - Adding visual clips (video, image, text, etc.) on top
    - Adding audio clips
    - Rendering the final video with multiprocessing support
    """

    def __init__(self, input_video: str, output_path: str):
        """
        Create a video composition.

        Args:
            input_video: Path to the base/background video
            output_path: Path where the final video will be saved
        """
        self._input: str = input_video
        self._output: str = output_path
        self._clips: List[Clip] = []
        self._audio_clips: List[AudioClip] = []

        self._load_input_properties()

    def _load_input_properties(self) -> None:
        """Load properties from the input video"""
        cap = cv2.VideoCapture(self._input)
        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video file: {self._input}")

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._input_fps = cap.get(cv2.CAP_PROP_FPS)
        self._input_total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if self._input_fps <= 0 or w <= 0 or h <= 0 or self._input_total_frames <= 0:
            cap.release()
            raise RuntimeError(f"Could not read valid properties from video: {self._input}")

        # Handle rotation
        # rotation = get_rotation(self._input)
        # if rotation == 90:
        #     self._rotation_flag = cv2.ROTATE_90_COUNTERCLOCKWISE
        #     self._input_size = (h, w)
        # elif rotation == 180:
        #     self._rotation_flag = cv2.ROTATE_180
        #     self._input_size = (w, h)
        # elif rotation == 270:
        #     self._rotation_flag = cv2.ROTATE_90_CLOCKWISE
        #     self._input_size = (h, w)
        # else:
        #     self._rotation_flag = None
        #     self._input_size = (w, h)

        get_logger().debug(f"Video dimensions: {self._input_size}")
        cap.release()

        self._output_from_frame = 0
        self._output_to_frame = self._input_total_frames

    def get_input_fps(self) -> float:
        """Get the FPS of the input video"""
        return self._input_fps

    def get_input_size(self) -> Tuple[int, int]:
        """Get the size (width, height) of the input video"""
        return self._input_size

    def get_input_duration(self) -> float:
        """Get the duration of the input video in seconds"""
        return self._input_total_frames / self._input_fps

    def cut_input(self, start: float, end: float) -> 'VideoComposition':
        """
        Cut the input video to a specific time range.

        Args:
            start: Start time in seconds
            end: End time in seconds

        Returns:
            Self for chaining
        """
        if start >= end or start < 0:
            raise ValueError(f"Invalid (start, end) for cutting video: ({start}, {end})")
        self._output_from_frame = int(start * self._input_fps)
        self._output_to_frame = int(end * self._input_fps)
        return self

    def add_clip(self, clip: Clip) -> 'VideoComposition':
        """
        Add a visual clip to the composition.

        Args:
            clip: Clip to add (VideoClip, ImageClip, TextClip, etc.)

        Returns:
            Self for chaining
        """
        self._clips.append(clip)
        return self

    def add_audio(self, audio_clip: AudioClip) -> 'VideoComposition':
        """
        Add an audio clip to the composition.

        Args:
            audio_clip: AudioClip to add

        Returns:
            Self for chaining
        """
        self._audio_clips.append(audio_clip)
        return self

    def render(
        self,
        use_multiprocessing: bool = True,
        processes: Optional[int] = None,
        video_quality: VideoQuality = VideoQuality.MIDDLE
    ) -> None:
        """
        Render the final video.

        Args:
            use_multiprocessing: Whether to use multiple processes for rendering
            processes: Number of processes to use (if None, uses CPU count)
            video_quality: Quality preset for encoding
        """
        temp_dir = tempfile.mkdtemp()

        try:
            if use_multiprocessing:
                processes = processes or mp.cpu_count()
                total_frames = self._output_to_frame - self._output_from_frame
                chunk_size = math.ceil(total_frames / processes)
                part_paths = []
                jobs = []

                for i in range(processes):
                    start = self._output_from_frame + i * chunk_size
                    end = min(self._output_from_frame + ((i+1) * chunk_size), self._output_to_frame)
                    part_path = os.path.join(temp_dir, f"part_{i}.mp4")
                    part_paths.append(part_path)

                    p = mp.Process(
                        target=self._render_range,
                        args=(start, end, part_path, video_quality)
                    )
                    jobs.append(p)
                    p.start()

                for p in jobs:
                    p.join()

                merged_parts = os.path.join(temp_dir, "merged_parts.mp4")
                self._merge_parts(part_paths, merged_parts)
                self._mux_audio(merged_parts, self._output)
            else:
                # Single-process
                tmp = os.path.join(temp_dir, "partial.mp4")
                self._render_range(self._output_from_frame, self._output_to_frame, tmp, video_quality)
                self._mux_audio(tmp, self._output)
        finally:
            shutil.rmtree(temp_dir)

        get_logger().info(f"Video saved to: {self._output}")

    def _render_range(self, start_frame: int, end_frame: int, part_path: str, video_quality: VideoQuality) -> None:
        """Render a range of frames"""
        cap = cv2.VideoCapture(self._input)
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        start_sec = start_frame / self._input_fps
        duration = (end_frame - start_frame) / self._input_fps

        ffmpeg_cmd = [
            "ffmpeg",
            "-y",
            # Input video
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self._input_size[0]}x{self._input_size[1]}",
            "-r", str(self._input_fps),
            "-i", "pipe:0",
            # Audio
            "-ss", str(start_sec),
            "-t", str(duration),
            "-i", self._input,
            # Maps
            "-map", "0:v",
            "-map", "1:a",
            # output codecs
            "-c:v", "libx264",
            "-preset", _get_ffmpeg_libx264_preset(video_quality),
            "-crf", _get_ffmpeg_libx264_crf(video_quality),
            "-c:a", "aac",
            # output config
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            part_path,
            # no logs
            "-loglevel", "error",
            "-hide_banner"
        ]

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE
        )

        num_frames_to_render = end_frame - start_frame
        with tqdm(total=num_frames_to_render, desc="Rendering video frames") as pbar:
            frame_idx = start_frame
            while frame_idx < end_frame:
                ret, frame = cap.read()
                if not ret:
                    break

                if self._rotation_flag is not None:
                    frame = cv2.rotate(frame, self._rotation_flag)

                # Render all clips onto the frame
                for clip in self._clips:
                    frame = clip.render(frame, frame_idx / self._input_fps)

                try:
                    process.stdin.write(frame.astype(np.uint8).tobytes())
                except BrokenPipeError:
                    get_logger().error("FFmpeg process died early.")
                    break

                frame_idx += 1
                pbar.update(1)

        cap.release()
        process.stdin.close()
        process.wait()

    def _merge_parts(self, part_paths: List[str], merged_path: str) -> None:
        """Merge multiple video parts into one"""
        list_path = os.path.join(os.path.dirname(merged_path), "parts.txt")
        with open(list_path, 'w') as f:
            for p in part_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            merged_path,
            "-loglevel", "error",
            "-hide_banner"
        ]
        subprocess.run(cmd, check=True)

    def _mux_audio(self, video_path: str, output_path: str, aac_bitrate: str = "192k") -> None:
        """Mix audio clips with the video"""
        if not self._audio_clips:
            shutil.copyfile(video_path, output_path)
            return

        from pydub import AudioSegment
        from pydub.effects import normalize

        try:
            main_audio = AudioSegment.from_file(video_path)
        except Exception as e:
            get_logger().error(f"Unable to extract audio from video. Ignoring audio clips. Pydub error: {e}")
            shutil.copyfile(video_path, output_path)
            return

        final_mix = main_audio
        for audio_clip in self._audio_clips:
            try:
                sfx = AudioSegment.from_file(audio_clip.path)

                # Apply volume
                if audio_clip.volume > 0:
                    db_change = 20 * math.log10(audio_clip.volume)
                    sfx = sfx + db_change
                else:
                    sfx = sfx - 100  # Effectively silence

                start_ms = audio_clip.start * 1000
                final_mix = final_mix.overlay(sfx, position=start_ms)

            except Exception as e:
                get_logger().warning(f"Unable to process audio clip: {audio_clip.path}. Error: {e}")
                continue

        normalized_mix = normalize(final_mix)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
            temp_audio_path = temp_audio_file.name

        try:
            normalized_mix.export(temp_audio_path, format="wav")
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", temp_audio_path,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", aac_bitrate,
                "-shortest",
                output_path,
                "-loglevel", "error",
                "-hide_banner"
            ]

            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            get_logger().error(f"Fatal error processing audio with ffmpeg: {e.stderr}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)


def _get_ffmpeg_libx264_preset(quality: VideoQuality) -> str:
    """Get ffmpeg preset for quality level"""
    mapping = {
        VideoQuality.LOW: 'ultrafast',
        VideoQuality.MIDDLE: 'veryfast',
        VideoQuality.HIGH: 'fast',
        VideoQuality.VERY_HIGH: 'slow',
    }
    return mapping.get(quality, 'veryfast')


def _get_ffmpeg_libx264_crf(quality: VideoQuality) -> str:
    """Get ffmpeg CRF value for quality level"""
    mapping = {
        VideoQuality.LOW: '23',
        VideoQuality.MIDDLE: '21',
        VideoQuality.HIGH: '19',
        VideoQuality.VERY_HIGH: '17',
    }
    return mapping.get(quality, '21')
