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

from app.services.quiz import QuizService
from app.workers.quiz_worker import QuizWorker

from app.schemas.quiz import QuizCreate

from app.services.chapter import ChapterService
from app.schemas.chapter import ChapterCreate

from ai.chapter_detection.pipeline import ChapterTopicPipeline
from ai.speech.speech_result import SpeechSegment

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
        quiz_service: QuizService,
        chapter_service: ChapterService,
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
        self.quiz_service = quiz_service
        self.quiz_worker = QuizWorker()
        self.chapter_service = chapter_service
        self.chapter_pipeline = ChapterTopicPipeline()
        
        
    def transcription_stage(
        self,
        job_id: int,
        video_id: int,
        file_path: str,
    ) -> tuple[Transcript, list[dict]]:
        """
        Run Whisper transcription and persist transcript.

        Also returns the raw per-segment ASR output (start/end/text/
        speaker) alongside the persisted Transcript - only the
        Transcript itself is new here, but this stage is the only
        place that still has access to segment-level timestamps
        before they would otherwise be discarded (the Transcript
        model only stores flattened text). chapter_stage() consumes
        these directly, so chapters are derived from the exact same
        transcription output without ever retranscribing the audio.
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
        return transcript, result.get("segments", [])
    
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
        
        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=98,
            current_step="Generating Embeddings",
        )

        logger.info(
            "Start embedding stage for video %s",
            video_id,
        )

        embeddings = self.embedding_worker.process(
            transcript=transcript.text,
            video_id=video_id,
        )

        if not embeddings:
            logger.warning(
                "No embeddings generated for video %s. "
                "Existing embeddings, if any, are left untouched.",
                video_id,
            )
            raise ValueError(
                "Failed to generate transcript embeddings."
            )

        # Generation succeeded: it is now safe to replace whatever
        # embeddings this video already had. Capture the old
        # vector_ids before deleting so FAISS knows exactly what to
        # drop during the rebuild.
        old_vector_ids = {
            embedding.vector_id
            for embedding in self.embedding_service.get_by_video_id(
                video_id,
            )
        }

        vectors = [
            embedding["vector"]
            for embedding in embeddings
        ]

        vector_ids = [
            embedding["vector_id"]
            for embedding in embeddings
        ]

        logger.info(
            "Replacing embeddings for video %s: %s existing "
            "vector(s) to remove, %s newly generated chunk(s).",
            video_id,
            len(old_vector_ids),
            len(embeddings),
        )

        self.embedding_service.delete_by_video_id(
            video_id,
        )

        vector_store = VectorStore(
            dimension=1024,
        )

        try:
            vector_store.replace(
                remove_vector_ids=old_vector_ids,
                vectors=vectors,
                vector_ids=vector_ids,
            )
        except Exception:
            logger.exception(
                "FAISS replacement failed for video %s after its "
                "%s old embedding row(s) were already deleted from "
                "the database. %s newly generated chunk(s) were not "
                "persisted to FAISS or the database. Leaving this "
                "as a failed processing job for the existing "
                "retry mechanism to reprocess from scratch.",
                video_id,
                len(old_vector_ids),
                len(embeddings),
            )
            raise

        try:
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
        except Exception:
            logger.exception(
                "FAISS replacement for video %s completed "
                "successfully (%s vector(s) persisted), but "
                "persisting the corresponding embedding rows to the "
                "database failed. FAISS and the database are now "
                "inconsistent for this video until the processing "
                "job is retried.",
                video_id,
                len(embeddings),
            )
            raise

        logger.info(
            "Embedding generation completed for video %s. "
            "Generated %s chunks.",
            video_id,
            len(embeddings),
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
    
    def quiz_stage(
        self,
        job_id: int,
        video_id: int,
        transcript: Transcript,
    ):

        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=99,
            current_step="Generating Quiz",
        )


        logger.info(
            "Start quiz stage",
        )


        quizzes = self.quiz_worker.process(
            transcript=transcript.text,
        )


        for quiz in quizzes:

            self.quiz_service.create_quiz(
                QuizCreate(
                    video_id=video_id,
                    type=quiz["type"],
                    question=quiz["question"],
                    answer=quiz["answer"],
                    options=quiz["options"],
                )
            )


        logger.info(
            "Quiz generation completed.",
        )


        return quizzes

    def chapter_stage(
        self,
        job_id: int,
        video_id: int,
        transcript_segments: list[dict],
    ):
        """
        Derive chapters/topics from the transcription's own segments
        (produced by transcription_stage - not retranscribed, and no
        embeddings are recomputed here beyond what topic/chapter
        detection itself needs). Persists via ChapterService, mirroring
        embedding_stage's replace-on-reprocess pattern: delete this
        video's existing chapters, then insert the newly detected
        ones, so reprocessing a video never accumulates duplicates.

        Chapter detection is an optional enhancement, not a required
        artifact of processing: an empty/degenerate transcript simply
        yields zero or one chapter (a valid, non-error outcome), so
        this stage does not raise on "nothing meaningful found".
        """

        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=99,
            current_step="Detecting Chapters",
        )

        logger.info(
            "Start chapter stage for video %s",
            video_id,
        )

        speech_segments = [
            SpeechSegment(
                start=segment["start"],
                end=segment["end"],
                text=segment.get("text", ""),
                speaker=segment.get("speaker"),
            )
            for segment in transcript_segments
        ]

        chapter_result = self.chapter_pipeline.run(
            segments=speech_segments,
            video_id=video_id,
        )

        self.chapter_service.delete_by_video_id(
            video_id,
        )

        for chapter in chapter_result.chapters:
            self.chapter_service.create_chapter(
                ChapterCreate(
                    video_id=video_id,
                    title=chapter.title,
                    start_time=chapter.start,
                    end_time=chapter.end,
                    summary=chapter.summary,
                )
            )

        logger.info(
            "Chapter detection completed for video %s. "
            "Generated %s chapter(s).",
            video_id,
            len(chapter_result.chapters),
        )

        return chapter_result.chapters

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

        transcript, transcript_segments = self.transcription_stage(
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

        self.quiz_stage(
            job_id=job_id,
            video_id=video_id,
            transcript=transcript,
        )

        self.chapter_stage(
            job_id=job_id,
            video_id=video_id,
            transcript_segments=transcript_segments,
        )

        self.video_service.update_status(
            video_id=video_id,
            status="processed",
        )

        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=100,
            current_step="Completed",
        )
        
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