import cv2
import numpy as np
import multiprocess as mp
import subprocess
import os
import tempfile
import math
import shutil
from typing import Tuple, List, Optional
from .media_element import MediaElement
from .audio_element import AudioElement
from pycaps.logger import logger
from pycaps.common import VideoQuality
from tqdm import tqdm
from .video_utils import get_rotation

# TODO: we need to create a new class VideoFile (or something like that)
#  then, the composer should receive a VideoFile instance
#  and, the VideoFile could have methods like "set_fps" or "set_size", to change the fps and the resolution
#  currently, we're not changing the input video fps/size, so we're working with the full video resolution received and theen
#  before saving, we are changing the resolution/fps for the output
#  this could be not the best approach... since if the input video has a big resolution, we would be working with that (instead the output res)
class VideoComposer:

    def __init__(self, input: str, output: str):
        self._input: str = input
        self._output: str = output
        self._elements: List[MediaElement] = []
        self._audio_elements: List[AudioElement] = []

        self._load_input_properties()
    
    def _load_input_properties(self) -> None:
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

        rotation = get_rotation(self._input)
        if rotation == 90:
            self._rotation_flag = cv2.ROTATE_90_COUNTERCLOCKWISE
            self._input_size = (h, w)
        elif rotation == 180:
            self._rotation_flag = cv2.ROTATE_180
            self._input_size = (w, h)
        elif rotation == 270:
            self._rotation_flag = cv2.ROTATE_90_CLOCKWISE
            self._input_size = (h, w)
        else:
            self._rotation_flag = None
            self._input_size = (w, h)

        logger().debug(f"Video dimensions: {self._input_size}")
        cap.release()

        self._output_from_frame = 0
        self._output_to_frame = self._input_total_frames

    def get_input_fps(self) -> float:
        return self._input_fps
    
    def get_input_size(self) -> Tuple[int, int]:
        return self._input_size
    
    def get_input_duration(self) -> float:
        return self._input_total_frames * self._input_fps
    
    def cut_input(self, start: float, end: float) -> None:
        if start >= end or start < 0:
            raise ValueError(f"Invalid (start, end) for cutting video: {start, end}")
        self._output_from_frame = int(start * self._input_fps)
        self._output_to_frame = int(end * self._input_fps)

    def add_element(self, element: MediaElement) -> None:
        self._elements.append(element)

    def add_audio(self, audio_element: AudioElement) -> None:
        """Schedule an audio file to start at start_time (seconds)."""
        self._audio_elements.append(audio_element)

    def _render_range(self, start_frame: int, end_frame: int, part_path: str, video_quality: VideoQuality) -> None:
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
            "-preset", get_ffmpeg_libx264_preset_for_quality(video_quality),
            "-crf", get_ffmpeg_libx264_crf_for_quality(video_quality),
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

                for el in self._elements:
                    frame = el.render(frame, frame_idx / self._input_fps)

                try:
                    process.stdin.write(frame.astype(np.uint8).tobytes())
                except BrokenPipeError:
                    logger().error("FFmpeg process died early.")
                    break

                frame_idx += 1
                pbar.update(1)

        cap.release()
        process.stdin.close()
        process.wait()

    def _merge_parts(self, part_paths: List[str], merged_path: str) -> None:
        # Create a concat file
        list_path = os.path.join(os.path.dirname(merged_path), "parts.txt")
        with open(list_path, 'w') as f:
            for p in part_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")
        # Merge using ffmpeg
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

    def _mux_audio(
        self,
        video_path: str,
        output_path: str,
        aac_bitrate: str = "192k"
    ) -> None:
        if not self._audio_elements:
            shutil.copyfile(video_path, output_path)
            return

        from pydub import AudioSegment
        from pydub.effects import normalize

        try:
            main_audio = AudioSegment.from_file(video_path)
        except Exception as e:
            logger().error(f"Unable to extract audio from video. Ignoring sound effects. Pydub error: {e}")
            self._copy_video(video_path, output_path)
            return

        final_mix = main_audio
        for audio in self._audio_elements:
            try:
                sfx = AudioSegment.from_file(audio.path)
                # Convertir el multiplicador de volumen a decibelios (dB), que es lo que pydub usa.
                if audio.volume > 0:
                    db_change = 20 * math.log10(audio.volume)
                    sfx = sfx + db_change
                else:
                    sfx = sfx - 100 # Reducir por 100 dB es efectivamente silencio

                start_ms = audio.start * 1000
                final_mix = final_mix.overlay(sfx, position=start_ms)

            except Exception as e:
                logger().warning(f"Unable to process sound effect: {audio.path}. Error: {e}")
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
            logger.error(f"Fatal error processing audio with ffmpeg: {e.stderr}")
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

    def render(self, use_multiprocessing: bool = True, processes: Optional[int] = None, video_quality: VideoQuality = VideoQuality.MIDDLE) -> None:
        temp_dir = tempfile.mkdtemp()

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
            final = self._output
            self._mux_audio(merged_parts, final)
        else:
            # Single-process
            tmp = os.path.join(temp_dir, "partial.mp4")
            self._render_range(self._output_from_frame, self._output_to_frame, tmp, video_quality)
            self._mux_audio(tmp, self._output)
        
        shutil.rmtree(temp_dir)


def get_ffmpeg_libx264_preset_for_quality(quality: 'VideoQuality') -> str:
    if quality == VideoQuality.LOW:
        return 'ultrafast'
    elif quality == VideoQuality.MIDDLE:
        return 'veryfast'
    elif quality == VideoQuality.HIGH:
        return 'fast'
    elif quality == VideoQuality.VERY_HIGH:
        return 'slow'

def get_ffmpeg_libx264_crf_for_quality(quality: 'VideoQuality') -> str:
    if quality == VideoQuality.LOW:
        return '23'
    elif quality == VideoQuality.MIDDLE:
        return '21'
    elif quality == VideoQuality.HIGH:
        return '19'
    elif quality == VideoQuality.VERY_HIGH:
        return '17'