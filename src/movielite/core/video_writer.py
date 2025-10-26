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
from .video_clip import VideoClip

class VideoWriter:
    """
    Write clips to a video file.

    This class handles:
    - Rendering visual clips (video, image, text, composite, etc.)
    - Mixing audio clips
    - Encoding the final video with multiprocessing support
    """

    def __init__(
            self,
            output_path: str,
            fps: float = 30,
            size: Tuple[int, int] = (1920, 1080),
            duration: Optional[float] = None,
            use_gpu: bool = False
        ):
        """
        Create a video writer.

        Args:
            output_path: Path where the final video will be saved
            fps: Frames per second for the output video
            size: Video dimensions (width, height)
            duration: Total duration in seconds (if None, auto-calculated from clips)
            use_gpu: Try to use GPU encoding (h264_nvenc) if available, fallback to CPU
        """
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError(f"Invalid video size: {size}. Width and height must be greater than 0.")

        self._output: str = output_path
        self._fps: float = fps
        self._size: Tuple[int, int] = size
        self._duration: Optional[float] = duration
        self._clips: List[Clip] = []
        self._audio_clips: List[AudioClip] = []
        self._use_gpu = use_gpu and _check_nvenc_available()

        if use_gpu and not self._use_gpu:
            get_logger().warning("GPU encoding (h264_nvenc) not available, using CPU (libx264)")

        get_logger().debug(f"VideoWriter created: output={output_path}, fps={fps}, size={size}, gpu={self._use_gpu}")

    def add_clips(self, clips: List[Clip]) -> 'VideoWriter':
        """
        Add multiple visual clips to the composition.

        Args:
            clips: List of Clip instances to add

        Returns:
            Self for chaining
        """
        for clip in clips:
            self.add_clip(clip)
        return self

    def add_clip(self, clip: Clip) -> 'VideoWriter':
        """
        Add a visual clip to the composition.

        Args:
            clip: Clip to add (VideoClip, ImageClip, TextClip, etc.)

        Returns:
            Self for chaining
        """
        if not isinstance(clip, Clip):
            raise TypeError(f"Expected Clip instance, got {type(clip)}")
        
        self._clips.append(clip)
        return self

    def add_audio(self, audio_clip: AudioClip) -> 'VideoWriter':
        """
        Add an audio clip to the composition.

        Args:
            audio_clip: AudioClip to add

        Returns:
            Self for chaining
        """
        self._audio_clips.append(audio_clip)
        return self

    def write(
        self,
        processes: int = 1,
        video_quality: VideoQuality = VideoQuality.MIDDLE
    ) -> None:
        """
        Render and write the final video.

        Args:
            use_multiprocessing: Whether to use multiple processes for rendering
            processes: Number of processes to use (if None, uses CPU count)
            video_quality: Quality preset for encoding
        """
        # Calculate duration if not specified
        if self._duration is None:
            if self._clips:
                self._duration = max(clip.end for clip in self._clips)
            else:
                raise ValueError("No clips added and no duration specified")

        if self._duration <= 0:
            raise ValueError(f"Invalid duration: {self._duration}")

        # Extract audio from video clips for full render path
        self._extract_video_audio()
        total_frames = int(self._duration * self._fps)
        temp_dir = tempfile.mkdtemp()

        try:
            if processes > 1:
                chunk_size = math.ceil(total_frames / processes)
                part_paths = []
                jobs = []

                for i in range(processes):
                    start_frame = i * chunk_size
                    end_frame = min((i + 1) * chunk_size, total_frames)
                    part_path = os.path.join(temp_dir, f"part_{i}.mp4")
                    part_paths.append(part_path)

                    p = mp.Process(
                        target=self._render_range,
                        args=(start_frame, end_frame, part_path, video_quality)
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
                self._render_range(0, total_frames, tmp, video_quality)
                self._mux_audio(tmp, self._output)
        finally:
            shutil.rmtree(temp_dir)

        get_logger().info(f"Video saved to: {self._output}")

    def _extract_video_audio(self) -> None:
        """
        Extract audio from video clips and add them to the audio mix.

        This ensures that when using ProcessedVideoClip (which only reads frames),
        the audio from the video is still included in the final output.
        """

        for clip in self._clips:
            # Only extract audio from video clips
            if isinstance(clip, VideoClip):
                audio_clip = AudioClip(
                    path=clip._path,
                    start=clip.start,
                    duration=clip.duration,
                    offset=clip._offset
                )
                self._audio_clips.append(audio_clip)
                get_logger().debug(f"Extracted audio from video clip: {clip._path}")

    def _get_background_clip_and_clips_to_blend(self, clips: list[Clip], current_time: float) -> tuple[Clip | None, list[Clip]]:
        """
        Find the first active clip that can be used as background optimization, and the clips to blend in the current time.

        Returns:
            Tuple of (background_clip, remaining_clips_to_blend)
            If no valid background found, returns (None, original_clips)
        """
        clips_to_blend = []
        background_clip = None
        searching_background = True
        for clip in clips:
            t_rel = current_time - clip.start

            if not (0 <= t_rel < clip.duration):
                continue

            if not searching_background:
                clips_to_blend.append(clip)
                continue

            if clip.size[0] != self._size[0] or clip.size[1] != self._size[1]:
                searching_background = False
                clips_to_blend.append(clip)
                continue
            
            if clip.has_any_transform:
                searching_background = False
                clips_to_blend.append(clip)
                continue 

            background_clip = clip

        return (background_clip, clips_to_blend)

    def _render_range(self, start_frame: int, end_frame: int, part_path: str, video_quality: VideoQuality) -> None:
        """
        Render a range of frames by reading each frame.
        """

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self._size[0]}x{self._size[1]}",
            "-r", str(self._fps),
            "-i", "pipe:0",
        ]

        if self._use_gpu:
            # GPU encoding (NVIDIA)
            ffmpeg_cmd.extend([
                "-c:v", "h264_nvenc",
                "-preset", _get_ffmpeg_nvenc_preset(video_quality),
                "-cq:v", _get_ffmpeg_nvenc_cq(video_quality),
            ])
        else:
            # CPU encoding
            ffmpeg_cmd.extend([
                "-c:v", "libx264",
                "-preset", _get_ffmpeg_libx264_preset(video_quality),
                "-crf", _get_ffmpeg_libx264_crf(video_quality),
            ])

        ffmpeg_cmd.extend([
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            part_path,
            "-loglevel", "error",
            "-hide_banner"
        ])

        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        num_frames_to_render = end_frame - start_frame
        update_interval = max(1, num_frames_to_render // 50)

        with tqdm(total=num_frames_to_render, desc="Rendering video frames") as pbar:
            frames_since_update = 0

            for frame_idx in range(start_frame, end_frame):
                current_time = frame_idx / self._fps

                background_clip, clips_to_blend = self._get_background_clip_and_clips_to_blend(self._clips, current_time)
                if background_clip:
                    frame = background_clip.get_frame(current_time - background_clip._start)
                    if clips_to_blend:
                        frame = frame.astype(np.float32)
                else:
                    frame = np.zeros((self._size[1], self._size[0], 3), dtype=np.float32)

                for clip in clips_to_blend:
                    frame = clip.render(frame, current_time)

                try:
                    process.stdin.write(frame.astype(np.uint8).tobytes())
                except BrokenPipeError:
                    get_logger().error("FFmpeg process died early.")
                    break

                frames_since_update += 1
                if frames_since_update >= update_interval:
                    pbar.update(frames_since_update)
                    frames_since_update = 0

            # Final update for remaining frames
            if frames_since_update > 0:
                pbar.update(frames_since_update)

        process.stdin.close()
        process.wait()

        # Close any ProcessedVideoClip instances we created
        for clip in self._clips:
            if isinstance(clip, VideoClip):
                clip.close()

    def _merge_parts(self, part_paths: List[str], merged_path: str) -> None:
        """Merge multiple video parts into one using ffmpeg concat."""
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
        """
        Mix audio clips with the video.

        Args:
            video_path: Path to the video file
            output_path: Where to save the final video with audio
            aac_bitrate: Bitrate for AAC audio encoding
        """
        if not self._audio_clips:
            shutil.copyfile(video_path, output_path)
            return

        from pydub import AudioSegment
        from pydub.effects import normalize

        # Create silent audio base matching video duration
        try:
            silence = AudioSegment.silent(duration=int(self._duration * 1000))
        except Exception as e:
            get_logger().error(f"Unable to create silent audio base. Pydub error: {e}")
            shutil.copyfile(video_path, output_path)
            return

        final_mix = silence
        for audio_clip in self._audio_clips:
            try:
                # Load audio file
                sfx = AudioSegment.from_file(audio_clip.path)

                # Apply offset if specified
                if audio_clip.offset > 0:
                    offset_ms = int(audio_clip.offset * 1000)
                    sfx = sfx[offset_ms:]

                # Apply duration limit if specified
                if audio_clip.duration is not None:
                    duration_ms = int(audio_clip.duration * 1000)
                    sfx = sfx[:duration_ms]

                # Apply volume
                if audio_clip.volume > 0:
                    db_change = 20 * math.log10(audio_clip.volume)
                    sfx = sfx + db_change
                else:
                    sfx = sfx - 100  # Effectively silence

                start_ms = int(audio_clip.start * 1000)
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
    """Get ffmpeg preset for quality level."""
    mapping = {
        VideoQuality.LOW: 'ultrafast',
        VideoQuality.MIDDLE: 'veryfast',
        VideoQuality.HIGH: 'fast',
        VideoQuality.VERY_HIGH: 'slow',
    }
    return mapping.get(quality, 'veryfast')


def _get_ffmpeg_libx264_crf(quality: VideoQuality) -> str:
    """Get ffmpeg CRF value for quality level."""
    mapping = {
        VideoQuality.LOW: '23',
        VideoQuality.MIDDLE: '21',
        VideoQuality.HIGH: '19',
        VideoQuality.VERY_HIGH: '17',
    }
    return mapping.get(quality, '21')


def _get_ffmpeg_nvenc_preset(quality: VideoQuality) -> str:
    """Get NVENC preset for quality level (p1-p7)."""
    mapping = {
        VideoQuality.LOW: 'p1',
        VideoQuality.MIDDLE: 'p4',
        VideoQuality.HIGH: 'p6',
        VideoQuality.VERY_HIGH: 'p7',
    }
    return mapping.get(quality, 'p4')


def _get_ffmpeg_nvenc_cq(quality: VideoQuality) -> str:
    """Get NVENC CQ value for quality level (0-51)."""
    mapping = {
        VideoQuality.LOW: '23',
        VideoQuality.MIDDLE: '21',
        VideoQuality.HIGH: '19',
        VideoQuality.VERY_HIGH: '17',
    }
    return mapping.get(quality, '21')

def _check_nvenc_available() -> bool:
    """Check if NVENC (GPU encoding) is available."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "h264_nvenc" in result.stdout
    except Exception:
        return False
