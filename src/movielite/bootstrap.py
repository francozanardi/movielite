import shutil

def _check_dependency(name: str) -> bool:
    return shutil.which(name) is not None

def check_dependencies():
    ffmpeg_found = _check_dependency("ffmpeg")
    ffprobe_found = _check_dependency("ffprobe")

    if ffmpeg_found and ffprobe_found:
        return

    missing = []
    if not ffmpeg_found:
        missing.append("ffmpeg")
    if not ffprobe_found:
        missing.append("ffprobe")
    
    missing_str = " and ".join(missing)
    
    error_message = (
        f"\n\n--- Pycaps Dependency Error ---\n"
        f"Could not find required command(s): {missing_str}\n\n"
        f"pycaps requires a full installation of FFmpeg (which includes both ffmpeg and ffprobe)\n"
        f"to be available in your system's PATH.\n\n"
        f"These are essential for audio and video processing.\n\n"
        f"To fix this, please:\n"
        f"  1. Download FFmpeg from the official site: https://ffmpeg.org/download.html\n"
        f"  2. Unzip it to a permanent location on your computer.\n"
        f"  3. Add the 'bin' directory from the unzipped folder to your system's PATH environment variable.\n\n"
        f"After installation, please restart your terminal or command prompt and try again."
        f"\n---------------------------------\n"
    )

    raise RuntimeError(error_message)
