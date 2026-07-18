import json
import subprocess

from backend.app.types.video_metadata import VideoMetadata

def extract_metadata(
    file_path: str,
) -> VideoMetadata:
    """
    Extract metadata from a video using FFprobe.
    """
    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        file_path,
    ]
    
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )
    metadata = json.loads(
        result.stdout,
    )
    video_stream = next(
        stream
        for stream in metadata["streams"]
        if stream["codec_type"] == "video"
    )
    duration = int(
        float(metadata["format"]["duration"])
    )
    width = video_stream["width"]
    height = video_stream["height"]
    codec = video_stream["codec_name"]
    fps_text = video_stream["r_frame_rate"]
    numerator, denominator = fps_text.split("/")
    fps = float(numerator) / float(denominator)
    return VideoMetadata(
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        codec=codec,
    )