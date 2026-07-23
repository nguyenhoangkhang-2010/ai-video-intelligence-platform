from app.utils.ffprobe import extract_metadata
from app.services.video import VideoService
from app.services.transcript import TranscriptService
from app.workers.transcription_worker import TranscriptionWorker

from app.schemas.transcript import TranscriptCreate

class VideoPipelineService:
    def __init__(
        self,
        video_service: VideoService,
        transcript_service: TranscriptService,
    ):
        self.video_service = video_service
        self.transcript_service = transcript_service
        self.transcription_worker = TranscriptionWorker()
        
    def transcription_stage(
        self,
        video_id: int,
        file_path: str,
    ):
        """
        Run Whisper transcription and persist transcript.
        """
        print("[Pipeline] Start transcription")
        result = self.transcription_worker.process(
            video_path=file_path,
        )
        print(
            f"[Pipeline] Language: {result['language']}"
        )
        transcript = self.transcript_service.create_transcript(
            TranscriptCreate(
                video_id=video_id,
                language=result["language"],
                text=result["text"],
            )
        )
        return transcript
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

        transcript = self.transcription_stage(
            video_id=video_id,
            file_path=file_path,
        )

        return transcript
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