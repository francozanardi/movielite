import subprocess
import json
from .logger import get_logger

def get_rotation(video_path: str) -> int:
    """
    Use ffprobe to detect video rotation metadata.

    Args:
        video_path: Path to the video file

    Returns:
        Rotation angle in degrees (0, 90, 180, 270)
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        video_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        data = json.loads(result.stdout)

        # Find video stream
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if video_stream:
            # Try to get rotation from tags
            if "tags" in video_stream and "rotate" in video_stream["tags"]:
                rotation = int(float(video_stream["tags"]["rotate"]))
                get_logger().debug(f"Video rotation metadata found in tags: {rotation} degrees")
                return rotation % 360

            # Try to get rotation from side_data_list
            if "side_data_list" in video_stream:
                for side_data in video_stream["side_data_list"]:
                    if side_data.get("side_data_type") == "Display Matrix" and "rotation" in side_data:
                        rotation = int(float(side_data["rotation"]))
                        get_logger().debug(f"Video rotation metadata found in side_data: {rotation} degrees")
                        return rotation % 360

        return 0

    except Exception as e:
        get_logger().warning(f"Could not get rotation metadata using ffprobe. Assuming 0 degrees. Error: {e}")
        return 0
