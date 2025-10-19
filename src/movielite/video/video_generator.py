from typing import Optional, Tuple
import os
import tempfile
from pycaps.common import Document, VideoQuality
from pycaps.logger import logger

class VideoGenerator:
    def __init__(self):
        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None
        self._audio_path: Optional[str] = None

        # State of video generation
        self._has_video_generation_started: bool = False
        self._video_quality: VideoQuality = VideoQuality.MIDDLE
        self._fragment_time: Optional[tuple[float, float]] = None

    def set_video_quality(self, quality: VideoQuality):
        self._video_quality = quality

    def set_fragment_time(self, fragment_time: tuple[float, float]):
        self._fragment_time = fragment_time

    def get_sanitized_fragment_time(self) -> Optional[tuple[float, float]]:
        if not self._has_video_generation_started:
            raise RuntimeError("Video generation has not started. Call start() first.")
        return self._fragment_time

    def start(self, input_video_path: str, output_video_path: str):
        from .render.video_composer import VideoComposer

        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Error: Input video file not found: {input_video_path}")

        self._input_video_path = input_video_path
        self._output_video_path = output_video_path
        self._video_composer = VideoComposer(self._input_video_path, self._output_video_path)
        self._sanitize_fragment_time()
        if self._fragment_time:
            self._video_composer.cut_input(self._fragment_time[0], self._fragment_time[1])

        self._audio_path = self._get_audio_path_to_transcribe()
        self._has_video_generation_started = True
    
    def _sanitize_fragment_time(self):
        if not self._fragment_time:
            return
        
        start = min(max(self._fragment_time[0], 0), self._video_composer.get_input_duration() - 2)
        end = min(max(self._fragment_time[1], 0), self._video_composer.get_input_duration())
        self._fragment_time = (start, end)

    def _get_audio_path_to_transcribe(self) -> str:
        from .render.audio_utils import extract_audio_for_whisper

        fd, temp_audio_file_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            start = self._fragment_time[0] if self._fragment_time else None
            end = self._fragment_time[1] if self._fragment_time else None
            extract_audio_for_whisper(self._input_video_path, temp_audio_file_path, start, end)
            logger().debug(f"Audio extracted to: {temp_audio_file_path}")
            return temp_audio_file_path
        except Exception as e:
            logger().error(f"Error extracting audio: {e}")
            self.close()
            raise e
        
    def get_audio_path(self) -> str:
        if not self._has_video_generation_started:
            raise RuntimeError("Video generation has not started. Call start() first.")
        if not self._audio_path:
            raise RuntimeError("Audio path is not set. This is an unexpected error.")
        
        return self._audio_path

    def get_video_size(self) -> Tuple[int, int]:
        if not self._has_video_generation_started:
            raise RuntimeError("Video generation has not started. Call start() first.")
        if not self._video_composer:
            raise RuntimeError("Video clip is not set. This is an unexpected error.")
        return self._video_composer.get_input_size()

    def generate(self, document: Document):
        if not self._has_video_generation_started:
            raise RuntimeError("Video generation has not started. Call start() first.")
        
        clips = document.get_media_clips()
        if not clips:
            logger().warning("No subtitle clips were generated. The original video (or with external audio if provided) will be saved.")

        for clip in clips:
            self._video_composer.add_element(clip)
        for sfx in document.sfxs:
            self._video_composer.add_audio(sfx)

        logger().debug(f"Writing final video to: {self._output_video_path}")
        self._video_composer.render(use_multiprocessing=False, video_quality=self._video_quality)
        
    def close(self):
        self._remove_audio_file_if_needed()
        self._has_video_generation_started = False

    def _remove_audio_file_if_needed(self):
        if not self._audio_path:
            return
        try:
            os.remove(self._audio_path)
            logger().debug(f"Temporary audio file deleted: {self._audio_path}")
        except Exception as e:
            logger().warning(f"Error deleting temporary audio file {self._audio_path}: {e}")
