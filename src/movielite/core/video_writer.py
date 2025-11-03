import numpy as np
import multiprocess as mp
import subprocess
import os
import tempfile
import math
import shutil
from typing import Tuple, List, Optional
from tqdm import tqdm
from .media_clip import MediaClip
from .graphic_clip import GraphicClip
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
        ):
        """
        Create a video writer.

        Args:
            output_path: Path where the final video will be saved
            fps: Frames per second for the output video
            size: Video dimensions (width, height)
            duration: Total duration in seconds (if None, auto-calculated from clips)
        """
        if size[0] <= 0 or size[1] <= 0:
            raise ValueError(f"Invalid video size: {size}. Width and height must be greater than 0.")

        self._output: str = output_path
        self._fps: float = fps
        self._size: Tuple[int, int] = size
        self._duration: Optional[float] = duration
        self._graphic_clips: List[GraphicClip] = []
        self._audio_clips: List[AudioClip] = []

        get_logger().debug(f"VideoWriter created: output={output_path}, fps={fps}, size={size}")

    def add_clips(self, clips: List[MediaClip]) -> 'VideoWriter':
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

    def add_clip(self, clip: MediaClip) -> 'VideoWriter':
        """
        Add a visual clip to the composition.

        Args:
            clip: MediaClip to add (VideoClip, AudioClip, ImageClip, TextClip, etc.)

        Returns:
            Self for chaining
        """
        if isinstance(clip, AudioClip):
            self._audio_clips.append(clip)
        elif isinstance(clip, GraphicClip):
            self._graphic_clips.append(clip)
            if isinstance(clip, VideoClip) and clip.audio.has_audio:
                self._audio_clips.append(clip.audio)
        else:
            raise TypeError(f"Unsupported clip type: {type(clip)}")
        
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
            if self._graphic_clips:
                self._duration = max(clip.end for clip in self._graphic_clips)
            else:
                raise ValueError("No clips added and no duration specified")

        if self._duration <= 0:
            raise ValueError(f"Invalid duration: {self._duration}")

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

    def _get_background_clip_and_clips_to_blend(self, clips: list[GraphicClip], current_time: float) -> tuple[GraphicClip | None, list[GraphicClip]]:
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

        # CPU encoding with libx264 | We will soon support other encodings
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

                background_clip, clips_to_blend = self._get_background_clip_and_clips_to_blend(self._graphic_clips, current_time)
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

        # Close any VideoClip instances we created
        for clip in self._graphic_clips:
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
        Mix audio clips with the video using numpy-based mixing.

        Args:
            video_path: Path to the video file
            output_path: Where to save the final video with audio
            aac_bitrate: Bitrate for AAC audio encoding
        """
        if not self._audio_clips:
            shutil.copyfile(video_path, output_path)
            return

        try:
            # Determine common sample rate (use highest among all clips)
            target_sample_rate = max(clip.sample_rate for clip in self._audio_clips)

            # Determine if we need stereo (if any clip is stereo, mix as stereo)
            target_channels = max(clip.channels for clip in self._audio_clips)

            # Create silent buffer matching video duration
            total_samples = int(self._duration * target_sample_rate)
            mixed_audio = np.zeros((total_samples, target_channels), dtype=np.float32)

            CHUNK_DURATION_SECONDS = 10.0  # Process audio in 10-second chunks

            total_chunks = sum(
                int(np.ceil(clip.duration / CHUNK_DURATION_SECONDS))
                for clip in self._audio_clips
            )

            with tqdm(total=total_chunks, desc="Mixing audio clips") as pbar:
                for audio_clip in self._audio_clips:
                    try:
                        for samples, chunk_start_time in audio_clip.iter_chunks(chunk_duration=CHUNK_DURATION_SECONDS):
                            if len(samples) == 0:
                                pbar.update(1)
                                continue

                            # Resample if needed
                            if audio_clip.sample_rate != target_sample_rate:
                                samples = self._resample_audio(samples, audio_clip.sample_rate, target_sample_rate)

                            # Convert mono to stereo if needed
                            if samples.shape[1] < target_channels:
                                samples = np.repeat(samples, target_channels, axis=1)
                            elif samples.shape[1] > target_channels:
                                # Downmix stereo to mono (average channels)
                                samples = samples.mean(axis=1, keepdims=True)

                            # Calculate position in the mix (chunk_start_time is absolute in file)
                            # We need to offset by audio_clip.start in the composition
                            relative_time = chunk_start_time - audio_clip.offset  # Time relative to clip start
                            abs_start_time = audio_clip.start + relative_time  # Time in composition
                            start_sample = int(abs_start_time * target_sample_rate)
                            end_sample = min(start_sample + len(samples), total_samples)

                            if start_sample >= total_samples or start_sample < 0:
                                pbar.update(1)
                                continue

                            # Clip samples to fit in the mix buffer
                            if start_sample < 0:
                                samples = samples[-start_sample:]
                                start_sample = 0

                            samples_to_add = samples[:end_sample - start_sample]
                            mixed_audio[start_sample:end_sample] += samples_to_add

                            pbar.update(1)

                    except Exception as e:
                        get_logger().warning(f"Unable to process audio clip: {audio_clip.path}. Error: {e}")
                        continue

            # Normalize to prevent clipping
            max_val = np.abs(mixed_audio).max()
            if max_val > 1.0:
                mixed_audio = mixed_audio / max_val

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                temp_audio_path = temp_audio_file.name

            try:
                # Convert float32 [-1, 1] to int16 for WAV export
                audio_int16 = (mixed_audio * 32767).astype(np.int16)

                ffmpeg_encode_cmd = [
                    "ffmpeg", "-y",
                    "-f", "s16le",  # 16-bit signed little-endian PCM
                    "-ar", str(target_sample_rate),
                    "-ac", str(target_channels),
                    "-i", "pipe:0",  # Read from stdin
                    temp_audio_path
                ]

                subprocess.run(
                    ffmpeg_encode_cmd,
                    input=audio_int16.tobytes(),
                    capture_output=True,
                    check=True
                )

                # Mux audio with video
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

        except Exception as e:
            get_logger().error(f"Unable to mix audio: {e}")
            shutil.copyfile(video_path, output_path)

    def _resample_audio(self, samples: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """
        Resample audio to a different sample rate using linear interpolation.

        Args:
            samples: Audio samples (n_samples, n_channels)
            orig_rate: Original sample rate
            target_rate: Target sample rate

        Returns:
            Resampled audio
        """
        if orig_rate == target_rate:
            return samples

        duration = len(samples) / orig_rate
        target_length = int(duration * target_rate)

        # Use linear interpolation for each channel
        resampled = np.zeros((target_length, samples.shape[1]), dtype=np.float32)

        for ch in range(samples.shape[1]):
            resampled[:, ch] = np.interp(
                np.linspace(0, len(samples) - 1, target_length),
                np.arange(len(samples)),
                samples[:, ch]
            )

        return resampled


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
