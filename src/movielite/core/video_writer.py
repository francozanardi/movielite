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

class VideoWriter:
    """
    Write clips to a video file.

    This class handles:
    - Rendering visual clips (video, image, text, composite, etc.)
    - Mixing audio clips
    - Encoding the final video with multiprocessing support

    Architecture:
    - VideoClip (no transformations) → Fast path with ffmpeg filters
    - ProcessedVideoClip (with transformations) → Slow path with frame reading
    """

    def __init__(self, output_path: str, fps: float = 30, size: Tuple[int, int] = (1920, 1080), duration: Optional[float] = None):
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
        self._clips: List[Clip] = []
        self._audio_clips: List[AudioClip] = []

        get_logger().debug(f"VideoWriter created: output={output_path}, fps={fps}, size={size}")

    def add_clip(self, clip: Clip) -> 'VideoWriter':
        """
        Add a visual clip to the composition.

        Args:
            clip: Clip to add (VideoClip, ImageClip, TextClip, CompositeClip, etc.)

        Returns:
            Self for chaining
        """
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
        use_multiprocessing: bool = False,
        processes: Optional[int] = None,
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

        # Check if we can use fast path (ffmpeg-only, no frame reading)
        if self._can_use_fast_path():
            get_logger().info("Using fast path: ffmpeg composition (no frame reading)")
            self._render_fast_path(video_quality)
            get_logger().info(f"Video saved to: {self._output}")
            return

        # Full render path (reads frames)
        get_logger().info("Using full render path: reading frames")
        total_frames = int(self._duration * self._fps)
        temp_dir = tempfile.mkdtemp()

        try:
            if use_multiprocessing:
                processes = processes or mp.cpu_count()
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

    def _can_use_fast_path(self) -> bool:
        """
        Check if we can use the fast path with ffmpeg filters.

        Fast path requirements:
        - NO ProcessedVideoClip instances (they require frame-level processing)
        - At least one VideoClip as base

        If these conditions are met, we can compose everything with ffmpeg
        without reading any video frames.
        """
        if not self._clips:
            return False

        from .processed_video_clip import ProcessedVideoClip
        from .video_clip import VideoClip

        # Check if ANY clip is a ProcessedVideoClip
        # for clip in self._clips:
        #     if isinstance(clip, ProcessedVideoClip):
        #         get_logger().debug("Fast path: DISABLED (contains ProcessedVideoClip)")
        #         return False

        # Need at least one VideoClip as base
        has_video_clip = any(isinstance(c, VideoClip) for c in self._clips)
        if not has_video_clip:
            get_logger().debug("Fast path: DISABLED (no VideoClip found)")
            return False

        get_logger().debug("Fast path: ENABLED")
        return True

    def _render_fast_path(self, video_quality: VideoQuality) -> None:
        """
        Render using ffmpeg filters only (no frame reading).

        Strategy:
        1. Compose all VideoClips using ffmpeg filter_complex
        2. Render non-VideoClips (text, images) onto transparent background
        3. Overlay everything together
        4. Mix audio
        """
        from .video_clip import VideoClip

        # Separate VideoClips from other clips
        video_clips = [c for c in self._clips if isinstance(c, VideoClip)]
        other_clips = [c for c in self._clips if not isinstance(c, VideoClip)]

        temp_dir = tempfile.mkdtemp()

        try:
            # Compose all VideoClips with ffmpeg
            composed_video_path = os.path.join(temp_dir, "composed_videos.mp4")
            self._compose_videos_with_ffmpeg(video_clips, composed_video_path, video_quality)

            # Render non-video overlays if any
            if other_clips:
                overlays_path = os.path.join(temp_dir, "overlays.mov")
                self._render_overlays_only(other_clips, overlays_path, video_quality)

                # Overlay everything together
                final_video = os.path.join(temp_dir, "final_with_overlays.mp4")
                self._overlay_on_video(composed_video_path, overlays_path, final_video, video_quality)

                # Mix audio
                self._mux_audio(final_video, self._output)
            else:
                # No overlays, just mix audio
                self._mux_audio(composed_video_path, self._output)

        finally:
            shutil.rmtree(temp_dir)

    def _compose_videos_with_ffmpeg(self, video_clips: List, output_path: str, video_quality: VideoQuality) -> None:
        """
        Compose multiple VideoClips using ffmpeg filter_complex.

        Generates a filter_complex that:
        1. Trims each video to its offset/duration
        2. Overlays them at their respective positions and times
        3. Preserves audio from all clips

        Args:
            video_clips: List of VideoClip instances
            output_path: Where to save the composed video
            video_quality: Quality preset for encoding
        """
        if not video_clips:
            raise ValueError("No video clips to compose")

        # Sort by start time
        sorted_clips: list[Clip] = sorted(video_clips, key=lambda c: c.start)

        if len(sorted_clips) == 1:
            # Single video: need to create proper canvas with timing
            clip = sorted_clips[0]

            # Extract the video segment first
            filter_parts = []

            # Create blank base video for full duration
            filter_parts.append(f"color=c=black:s={self._size[0]}x{self._size[1]}:d={self._duration}:r={self._fps}[base]")

            # Trim video and set timing
            filter_parts.append(f"[0:v]setpts=PTS-STARTPTS+{clip.start}/TB[v0]")

            # Overlay at the correct time
            filter_parts.append(
                f"[base][v0]overlay=x=0:y=0:enable='between(t,{clip.start},{clip.end})'[out]"
            )

            # Extract and delay audio
            filter_parts.append(f"[0:a]adelay={int(clip.start * 1000)}|{int(clip.start * 1000)}[a0]")

            filter_complex = ";".join(filter_parts)

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(clip._offset),
                "-t", str(clip.duration),
                "-i", clip._path,
                "-filter_complex", filter_complex,
                "-map", "[out]",
                "-map", "[a0]",
                "-c:v", "libx264",
                "-preset", _get_ffmpeg_libx264_preset(video_quality),
                "-crf", _get_ffmpeg_libx264_crf(video_quality),
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-pix_fmt", "yuv420p",
                output_path,
                "-loglevel", "error",
                "-hide_banner"
            ]
            subprocess.run(cmd, check=True)
            return

        # Multiple videos: build filter_complex
        # Strategy: Create a blank canvas, then overlay each video at its time

        inputs = []
        filter_parts = []

        # Add all video inputs
        for i, clip in enumerate(sorted_clips):
            inputs.extend(["-ss", str(clip._offset), "-t", str(clip.duration), "-i", clip._path])

        # Create blank base video
        filter_parts.append(f"color=c=black:s={self._size[0]}x{self._size[1]}:d={self._duration}:r={self._fps}[base]")

        # Overlay each video on top
        current_layer = "base"
        for i, clip in enumerate(sorted_clips):
            # Trim and set timing for this video
            filter_parts.append(f"[{i}:v]setpts=PTS-STARTPTS+{clip.start}/TB[v{i}]")

            # Overlay it
            next_layer = f"tmp{i}" if i < len(sorted_clips) - 1 else "out"
            # Enable overlay only during the clip's time range
            filter_parts.append(
                f"[{current_layer}][v{i}]overlay=x=0:y=0:enable='between(t,{clip.start},{clip.end})'[{next_layer}]"
            )
            current_layer = next_layer

        # Mix audio: delay each audio track and mix them
        for i, clip in enumerate(sorted_clips):
            delay_ms = int(clip.start * 1000)
            filter_parts.append(f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

        # Mix all delayed audio tracks
        audio_inputs = "".join(f"[a{i}]" for i in range(len(sorted_clips)))
        filter_parts.append(f"{audio_inputs}amix=inputs={len(sorted_clips)}:duration=longest[aout]")

        filter_complex = ";".join(filter_parts)

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", _get_ffmpeg_libx264_preset(video_quality),
            "-crf", _get_ffmpeg_libx264_crf(video_quality),
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            output_path,
            "-loglevel", "error",
            "-hide_banner"
        ]

        get_logger().debug(f"FFmpeg filter_complex: {filter_complex}")
        subprocess.run(cmd, check=True)

    def _render_overlays_only(self, overlay_clips: List[Clip], output_path: str, video_quality: VideoQuality) -> None:
        """
        Render non-video clips (text, images) onto a transparent background.

        Uses PNG codec to preserve alpha channel for proper overlay composition.
        """
        from .video_clip import VideoClip
        from .processed_video_clip import ProcessedVideoClip

        # Convert any VideoClip to ProcessedVideoClip for frame rendering
        clips_to_render: list[Clip] = []
        for clip in overlay_clips:
            if isinstance(clip, VideoClip) and not isinstance(clip, ProcessedVideoClip):
                processed = ProcessedVideoClip.from_video_clip(clip)
                clips_to_render.append(processed)
            else:
                clips_to_render.append(clip)

        total_frames = int(self._duration * self._fps)

        # Use QuickTime Animation (qtrle) codec to preserve alpha
        # PNG is lossless but creates huge files, qtrle is a good compromise
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgra",
            "-s", f"{self._size[0]}x{self._size[1]}",
            "-r", str(self._fps),
            "-i", "-",
            "-c:v", "qtrle",  # QuickTime Animation codec with alpha
            output_path,
            "-loglevel", "error",
            "-hide_banner"
        ]

        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        with tqdm(total=total_frames, desc="Rendering overlays") as pbar:
            for frame_idx in range(total_frames):
                # Create transparent frame
                frame = np.zeros((self._size[1], self._size[0], 4), dtype=np.float32)

                current_time = frame_idx / self._fps
                for clip in clips_to_render:
                    frame = clip.render(frame, current_time)

                process.stdin.write(frame.astype(np.uint8).tobytes())
                pbar.update(1)

        process.stdin.close()
        process.wait()

        # Close any ProcessedVideoClip instances we created
        for clip in clips_to_render:
            if isinstance(clip, ProcessedVideoClip):
                clip.close()

    def _overlay_on_video(self, base_video_path: str, overlay_path: str, output_path: str, video_quality: VideoQuality) -> None:
        """
        Overlay rendered overlays onto the base video using ffmpeg.

        Args:
            base_video_path: Path to the base video
            overlay_path: Path to the overlay video (with alpha channel)
            output_path: Where to save the result
            video_quality: Quality preset for encoding
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", base_video_path,
            "-i", overlay_path,
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", "libx264",
            "-preset", _get_ffmpeg_libx264_preset(video_quality),
            "-crf", _get_ffmpeg_libx264_crf(video_quality),
            "-c:a", "copy",
            "-movflags", "+faststart",
            output_path,
            "-loglevel", "error",
            "-hide_banner"
        ]

        subprocess.run(cmd, check=True)

    def _render_range(self, start_frame: int, end_frame: int, part_path: str, video_quality: VideoQuality) -> None:
        """
        Render a range of frames by reading each frame.

        Used in full render path when ProcessedVideoClip is present.
        """
        from .video_clip import VideoClip
        from .processed_video_clip import ProcessedVideoClip

        # Convert any VideoClip to ProcessedVideoClip for frame rendering
        clips_to_render: list[Clip] = []
        for clip in self._clips:
            if isinstance(clip, VideoClip) and not isinstance(clip, ProcessedVideoClip):
                processed = ProcessedVideoClip.from_video_clip(clip)
                clips_to_render.append(processed)
            else:
                clips_to_render.append(clip)

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "bgr24",
            "-s", f"{self._size[0]}x{self._size[1]}",
            "-r", str(self._fps),
            "-i", "pipe:0",
            "-c:v", "libx264",
            "-preset", _get_ffmpeg_libx264_preset(video_quality),
            "-crf", _get_ffmpeg_libx264_crf(video_quality),
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            part_path,
            "-loglevel", "error",
            "-hide_banner"
        ]

        process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        num_frames_to_render = end_frame - start_frame
        with tqdm(total=num_frames_to_render, desc="Rendering video frames") as pbar:
            for frame_idx in range(start_frame, end_frame):
                # Create black frame
                frame = np.zeros((self._size[1], self._size[0], 3), dtype=np.float32)

                # Render all clips onto the frame
                current_time = frame_idx / self._fps
                for clip in clips_to_render:
                    frame = clip.render(frame, current_time)

                # Convert to uint8 and write
                try:
                    process.stdin.write(frame.astype(np.uint8).tobytes())
                except BrokenPipeError:
                    get_logger().error("FFmpeg process died early.")
                    break

                pbar.update(1)

        process.stdin.close()
        process.wait()

        # Close any ProcessedVideoClip instances we created
        for clip in clips_to_render:
            if isinstance(clip, ProcessedVideoClip):
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
