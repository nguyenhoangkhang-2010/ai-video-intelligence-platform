import json
import subprocess

from app.pipelines.video_pipiline import(
    VideoPipelineService
)

def process_video(
    video_id: int,
    file_path: str,
):
    pipeline = VideoPipelineService()

    pipeline.process(
        video_id,
        file_path,
    )
    
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