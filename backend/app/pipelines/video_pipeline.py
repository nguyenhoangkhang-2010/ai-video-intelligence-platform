import logging

from app.utils.ffprobe import extract_metadata
from app.services.video import VideoService
from app.services.processing_job import ProcessingJobService
from app.services.transcript import TranscriptService
from app.workers.transcription_worker import TranscriptionWorker

from app.schemas.transcript import TranscriptCreate
from app.models.transcript import Transcript

from app.services.summary import SummaryService
from app.workers.summary_worker import SummaryWorker

from app.schemas.summary import SummaryCreate
from app.models.summary import Summary

from app.services.embedding import EmbeddingService
from app.workers.embedding_worker import EmbeddingWorker

from app.schemas.embedding import EmbeddingCreate

from app.services.translation import TranslationService
from app.workers.translation_worker import TranslationWorker

from app.schemas.translation import TranslationCreate
from app.models.translation import Translation

from ai.embedding.vector_store import VectorStore

logger = logging.getLogger(__name__)


class VideoPipelineService:
    """
    AI processing pipeline for uploaded videos.
    """
    def __init__(
        self,
        video_service: VideoService,
        transcript_service: TranscriptService,
        summary_service: SummaryService,
        embedding_service: EmbeddingService,
        translation_service: TranslationService,
        processing_job_service: ProcessingJobService,
    ):
        self.video_service = video_service
        self.transcript_service = transcript_service
        self.processing_job_service = processing_job_service
        self.summary_service = summary_service
        self.embedding_service = embedding_service
        self.translation_service = translation_service
        self.summary_worker = SummaryWorker()
        self.embedding_worker = EmbeddingWorker()
        self.translation_worker = TranslationWorker()
        self.transcription_worker = TranscriptionWorker()
        
        
    def transcription_stage(
        self,
        job_id: int,
        video_id: int,
        file_path: str,
    ) -> Transcript:
        """
        Run Whisper transcription and persist transcript.
        """
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=25,
            current_step="Preparing Transcription",
        )
        
        logger.info(
            "Start transcription stage"
        )
        
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=70,
            current_step="Transcribing",
        )
        
        result = self.transcription_worker.process(
            video_path=file_path,
        )
        
        if not result["text"].strip():
            logger.warning(
                "No speech detected in video %s",
                video_id,
            )
            raise ValueError(
                "No speech detected in audio."
            )
        
        logger.info(
            "Detected language: %s",
            result["language"],
        )
        
        self.video_service.update_processing_result(
            video_id=video_id,
            language=result["language"],
            status="processed",
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
    
    def summary_stage(
        self,
        job_id: int,
        video_id: int,
        transcript: Transcript,
    ) -> Summary:
        """
        Generate summary from transcript.
        """
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=95,
            current_step="Generating Summary",
        )

        logger.info(
            "Start summary stage",
        )

        result = self.summary_worker.process(
            transcript=transcript.text,
        )

        summary = self.summary_service.create_summary(
            SummaryCreate(
                video_id=video_id,
                type=result["type"],
                content=result["content"],
                model_name=result["model_name"],
            )
        )

        logger.info(
            "Summary generated.",
        )

        return summary
    
    def embedding_stage(
        self,
        job_id: int,
        video_id: int,
        transcript: Transcript,
    ):
        """
        Generate embeddings from transcript.
        """
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=98,
            current_step="Generating Embeddings",
        )

        logger.info(
            "Start embedding stage",
        )

        embeddings = self.embedding_worker.process(
            transcript=transcript.text,
        )
        
        vector_store = VectorStore(
            dimension=1024,
        )

        vector_store.add(
            [
                embedding["vector"]
                for embedding in embeddings
            ],
            vector_ids=[
                embedding["vector_id"]
                for embedding in embeddings
            ],
        )

        for embedding in embeddings:
            self.embedding_service.create_embedding(
                EmbeddingCreate(
                    video_id=video_id,
                    chunk_index=embedding["chunk_index"],
                    chunk_text=embedding["chunk_text"],
                    embedding_model=embedding["embedding_model"],
                    vector_id=embedding["vector_id"],
                )
            )

        logger.info(
            "Embedding generation completed.",
        )
        
        return embeddings
    
    def translation_stage(
        self,
        job_id: int,
        video_id: int,
        transcript: Transcript,
    ) -> Translation:
        """
        Generate translated subtitle.
        """

        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=99,
            current_step="Generating Translation",
        )

        logger.info(
            "Start translation stage",
        )

        result = self.translation_worker.process(
            transcript=transcript.text,
            target_language="en",
        )

        translation = self.translation_service.create_translation(
            TranslationCreate(
                video_id=video_id,
                language=result["language"],
                subtitle=result["subtitle"],
            )
        )

        logger.info(
            "Translation completed.",
        )

        return translation
    
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

        self.summary_stage(
            job_id=job_id,
            video_id=video_id,
            transcript=transcript,
        )
        
        self.embedding_stage(
            job_id=job_id,
            video_id=video_id,
            transcript=transcript,
        )
        
        self.translation_stage(
            job_id=job_id,
            video_id=video_id,
            transcript=transcript,
        )

        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=100,
            current_step="Completed",
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
        logger.info(
            "Extract metadata for video %s",
            video_id,
        )

        metadata = extract_metadata(file_path)

        logger.info(
            "Metadata extraction completed for video %s",
            metadata,
        )
        self.video_service.update_metadata(
            video_id=video_id,
            metadata=metadata,
        )