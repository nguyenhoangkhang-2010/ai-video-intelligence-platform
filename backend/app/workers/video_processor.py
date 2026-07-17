import time


def process_video(
    video_id: int,
):
    """
    Simulate AI video processing.
    This worker will later run:
    - FFmpeg
    - Whisper
    - GPT Summary
    - Embedding
    """
    print(f"Start processing video {video_id}")
    time.sleep(10)
    print(f"Finished processing video {video_id}")