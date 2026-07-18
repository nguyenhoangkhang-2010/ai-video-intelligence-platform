import json
import subprocess

from app.pipelines.video_pipeline import(
    VideoPipelineService
)

def process_video(
    video_id: int,
    file_path: str,
):
    pipeline = VideoPipelineService()

    pipeline.process(
        video_id= video_id,
        file_path= file_path,
    )