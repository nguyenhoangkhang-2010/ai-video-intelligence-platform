from app.utils.ffprobe import extract_metadata
from app.services.video import VideoService

class VideoPipelineService:
    def __init__(
        self,
        video_service: VideoService,
    ):
        self.video_service = video_service
    """
    AI processing pipeline for uploaded videos.
    """
    def process(
        self,
        video_id: int,
        file_path: str,
    ):
        """
        Execute the complete AI pipeline.
        """
        self.metadata_stage(
            video_id=video_id,
            file_path=file_path,
        )
        # TODO
        # self.transcribe()
        # TODO
        # self.generate_summary()
        # TODO
        # self.create_embeddings()
        # TODO
        # self.translate()
        # TODO
        # self.generate_quiz()
        # TODO
        # self.generate_flashcards()
        
    def metadata_stage(
        self,
        video_id: int,
        file_path: str,
    ):
        """
        Extract video metadata using FFprobe.
        """
        print(f"[Pipeline] Extract metadata for video {video_id}")
        metadata = extract_metadata(file_path)
        print(metadata)
        self.video_service.update_metadata(
            video_id=video_id,
            metadata=metadata,
        )