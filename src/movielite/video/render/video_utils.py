import subprocess
from pycaps.logger import logger
import json

def get_rotation(video_path) -> int:
    """
    Use ffprobe to detect video rotation metadata by requesting JSON output.
    Returns the rotation angle in degrees (e.g., 90, 180, 270).
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
        
        # First we search for the 'video' stream (it may contain different streams like audio, video, etc.)
        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break
        
        if video_stream:
            # First we try to get the rotation from the tags
            if "tags" in video_stream and "rotate" in video_stream["tags"]:
                rotation = int(float(video_stream["tags"]["rotate"]))
                logger().debug(f"Video rotation metadata found in tags: {rotation} degrees")
                return rotation % 360

            # If we didn't find it in the tags, we try searching in the 'side_data_list' property.
            if "side_data_list" in video_stream:
                for side_data in video_stream["side_data_list"]:
                    if side_data.get("side_data_type") == "Display Matrix" and "rotation" in side_data:
                        rotation = int(float(side_data["rotation"]))
                        logger().debug(f"Video rotation metadata found in side_data: {rotation} degrees")
                        return rotation % 360

        return 0

    except Exception as e:
        logger().warning(f"Could not get rotation metadata using ffprobe. Assuming 0 degrees. Error: {e}")
        return 0
