from app.utils.ffprobe import extract_metadata
from app.services.video import VideoService
from app.services.processing_job import ProcessingJobService
from app.services.transcript import TranscriptService
from app.workers.transcription_worker import TranscriptionWorker

from app.schemas.transcript import TranscriptCreate

class VideoPipelineService:
    """
    AI processing pipeline for uploaded videos.
    """
    def __init__(
        self,
        video_service: VideoService,
        transcript_service: TranscriptService,
        processing_job_service: ProcessingJobService,
    ):
        self.video_service = video_service
        self.transcript_service = transcript_service
        self.processing_job_service = processing_job_service
        self.transcription_worker = TranscriptionWorker()
        
    def transcription_stage(
        self,
        job_id: int,
        video_id: int,
        file_path: str,
    ):
        """
        Run Whisper transcription and persist transcript.
        """
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=25,
            current_step="Extract Audio",
        )
        
        print("[Pipeline] Start transcription")
        
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=70,
            current_step="Transcribing",
        )
        
        result = self.transcription_worker.process(
            video_path=file_path,
        )
        
        print(
            f"[Pipeline] Language: {result['language']}"
        )
        
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=90,
            current_step="Saving Transcript",
        )
        
        transcript = self.transcript_service.create_transcript(
            TranscriptCreate(
                video_id=video_id,
                language=result["language"],
                text=result["text"],
            )
        )
        return transcript
    
    def process(
        self,
        job_id: int,
        video_id: int,
        file_path: str,
    ):
        """
        Execute the complete AI pipeline.
        """
        self.metadata_stage(
            job_id=job_id,
            video_id=video_id,
            file_path=file_path,
        )

        transcript = self.transcription_stage(
            job_id=job_id,
            video_id=video_id,
            file_path=file_path,
        )

        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=100,
            current_step="Completed",
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
        job_id: int,
        video_id: int,
        file_path: str,
    ):
        """
        Extract video metadata using FFprobe.
        """
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=10,
            current_step="Extract Metadata",
        )
        print(f"[Pipeline] Extract metadata for video {video_id}")
        metadata = extract_metadata(file_path)
        print(metadata)
        self.video_service.update_metadata(
            video_id=video_id,
            metadata=metadata,
        )