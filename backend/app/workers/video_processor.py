import json
import subprocess

def process_video(
    video_id: int,
    file_path: str,
):
    """
    Background task for processing uploaded video.

    TODO:
    - Extract metadata using FFprobe
    - Transcribe audio using Whisper
    - Generate summary using LLM
    - Create embeddings
    """

    print(f"Start processing video {video_id}")

    duration = extract_duration(file_path)

    print(f"Duration: {duration} seconds")

    print(f"Finished processing video {video_id}")
    
def extract_duration(
    file_path: str,
) -> int:
    """
    Extract video duration using ffprobe.
    """

    command = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        file_path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    metadata = json.loads(result.stdout)

    duration = float(
        metadata["format"]["duration"]
    )

    return int(duration)