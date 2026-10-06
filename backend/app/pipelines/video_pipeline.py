import logging

from app.core.retry import is_transient_error
from app.pipelines.stage_definitions import (
    CHAPTER,
    EMBEDDING,
    FLASHCARD,
    METADATA,
    QUIZ,
    STAGE_DEPENDENCIES,
    STAGE_ORDER,
    SUMMARY,
    TRANSCRIPTION,
    TRANSLATION,
)
from app.storage.base import StorageBackend
from app.utils.ffprobe import extract_metadata
from app.utils.thumbnail import extract_thumbnail
from app.services.video import VideoService
from app.services.processing_job import ProcessingJobService
from app.services.processing_stage import ProcessingStageService
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

from app.services.flashcard import FlashcardService
from app.workers.flashcard_worker import FlashcardWorker

from app.schemas.flashcard import FlashcardCreate

from ai.chapter_detection.pipeline import ChapterTopicPipeline
from ai.speech.speech_result import SpeechSegment

logger = logging.getLogger(__name__)


class ProcessingIncompleteError(Exception):
    """
    Raised by VideoPipelineService.process() when the stage loop
    finishes with one or more stages not COMPLETED/SKIPPED, but no
    single exception was collected this run to re-raise directly
    (e.g. every eligible stage already exhausted its retry budget, or
    every remaining incomplete stage was blocked by a dependency that
    never succeeded). Never classified as transient - retrying the
    task again would not change anything an exception was already
    raised for.
    """


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
        processing_stage_service: ProcessingStageService,
        quiz_service: QuizService,
        chapter_service: ChapterService,
        flashcard_service: FlashcardService,
        storage: StorageBackend,
    ):
        self.video_service = video_service
        self.storage = storage
        self.transcript_service = transcript_service
        self.processing_job_service = processing_job_service
        self.processing_stage_service = processing_stage_service
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
        self.flashcard_service = flashcard_service
        self.flashcard_worker = FlashcardWorker()


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
        
        # save_transcript (upsert) rather than create_transcript: a
        # reprocessed video must get its transcript genuinely
        # regenerated, not silently keep whatever the first attempt
        # produced. transcripts.video_id stays UNIQUE at the DB level
        # regardless (see migration), so this is still exactly one
        # row per video, just atomically replaced on reprocess instead
        # of frozen on first write.
        transcript = self.transcript_service.save_transcript(
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

        # save_summary (upsert) rather than create_summary: a
        # reprocessed video must get a genuinely regenerated summary,
        # not silently keep a prior attempt's content. Uniqueness on
        # (video_id, type) stays DB-enforced (see migration); this
        # only changes what happens when a row for that key already
        # exists - replace it, not skip it.
        summary = self.summary_service.save_summary(
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

        # FAISS is written FIRST, before anything in Postgres changes.
        # This is deliberate: if this raises, no database row for this
        # video has been touched yet, so the old embeddings stay fully
        # valid and searchable - the failure is a clean no-op instead
        # of leaving the DB emptied out from under a FAISS index that
        # was never actually updated (the previous ordering's failure
        # mode). VectorStore.replace() is itself atomic at the file
        # level (temp-write + rename for both the index and its
        # metadata sidecar), so a crash mid-replace can never leave a
        # half-written index on disk either.
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
                "FAISS replacement failed for video %s. No database "
                "rows were touched - this video's existing "
                "embeddings remain valid and searchable. Leaving "
                "this as a failed processing job for the existing "
                "retry mechanism to reprocess from scratch.",
                video_id,
            )
            raise

        # Only after FAISS holds the new vectors do we touch Postgres,
        # and the delete-old+insert-new happens in a single transaction
        # (EmbeddingRepository.replace_for_video) rather than a delete
        # followed by a per-row insert loop: a failure here can now
        # only land as "every old row still present" (rollback) or
        # "every new row present" (commit) - never a partial mix.
        #
        # If this raises, Postgres rolls back to the OLD rows, which
        # point at vector_ids FAISS no longer has (already replaced
        # above) - this video is unsearchable until the job is
        # retried. That retry is self-healing: Embedder's vector_ids
        # are deterministic (see ai.embedding.embedder), so
        # re-running this stage regenerates the identical vector_ids,
        # VectorStore.replace() treats them as already-present
        # duplicates (no-op for FAISS), and only the Postgres write is
        # actually retried.
        try:
            self.embedding_service.replace_for_video(
                video_id,
                [
                    EmbeddingCreate(
                        video_id=video_id,
                        chunk_index=embedding["chunk_index"],
                        chunk_text=embedding["chunk_text"],
                        embedding_model=embedding["embedding_model"],
                        vector_id=embedding["vector_id"],
                    )
                    for embedding in embeddings
                ],
            )
        except Exception:
            logger.exception(
                "FAISS replacement for video %s completed "
                "successfully (%s vector(s) persisted), but "
                "persisting the corresponding embedding rows to the "
                "database failed and was rolled back. FAISS and the "
                "database are now inconsistent for this video until "
                "the processing job is retried.",
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
            source_language=transcript.language,
        )

        # save_translation (upsert) rather than create_translation:
        # a reprocessed video must get a genuinely regenerated
        # translation for that language, not silently keep a prior
        # attempt's text. Uniqueness on (video_id, language) stays
        # DB-enforced (see migration); this only changes what happens
        # when a row for that key already exists - replace it, not
        # skip it.
        translation = self.translation_service.save_translation(
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
        """
        Generate and persist quiz questions from the transcript.

        Idempotent by atomic replacement: this video's quiz set is
        replaced in a single transaction (QuizRepository.
        replace_for_video) rather than deleted then inserted row by
        row, so a crash partway through can never leave this video
        with a partial mix of old and new quizzes - either the old
        set is still fully intact (on failure) or the new set is
        fully present (on success). The LLM's output is not
        deterministic across retries; that is expected and fine -
        idempotency here means "one logical attempt, one complete
        artifact set," not "identical text every time."
        """

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

        self.quiz_service.replace_for_video(
            video_id,
            [
                QuizCreate(
                    video_id=video_id,
                    type=quiz["type"],
                    question=quiz["question"],
                    answer=quiz["answer"],
                    options=quiz["options"],
                )
                for quiz in quizzes
            ],
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

        # Idempotent by atomic replacement (see quiz_stage's docstring
        # for the same rationale) - this video's chapter set is
        # replaced in one transaction rather than deleted then
        # inserted row by row, including the empty-list case (zero
        # chapters is a valid outcome - see this method's own
        # docstring - and must still atomically clear any stale
        # chapters from a previous attempt).
        self.chapter_service.replace_for_video(
            video_id,
            [
                ChapterCreate(
                    video_id=video_id,
                    title=chapter.title,
                    start_time=chapter.start,
                    end_time=chapter.end,
                    summary=chapter.summary,
                )
                for chapter in chapter_result.chapters
            ],
        )

        logger.info(
            "Chapter detection completed for video %s. "
            "Generated %s chapter(s).",
            video_id,
            len(chapter_result.chapters),
        )

        return chapter_result.chapters

    def flashcard_stage(
        self,
        job_id: int,
        video_id: int,
        transcript: Transcript,
    ):
        """
        Generate and persist study flashcards from the transcript.

        Idempotent by atomic replacement (see quiz_stage's docstring
        for the same rationale) - this video's flashcard set is
        replaced in one transaction rather than deleted then inserted
        row by row.
        """

        self.processing_job_service.update_progress(
            job_id=job_id,
            progress=99,
            current_step="Generating Flashcards",
        )

        logger.info(
            "Start flashcard stage for video %s",
            video_id,
        )

        flashcards = self.flashcard_worker.process(
            transcript=transcript.text,
        )

        self.flashcard_service.replace_for_video(
            video_id,
            [
                FlashcardCreate(
                    video_id=video_id,
                    question=flashcard["question"],
                    answer=flashcard["answer"],
                    difficulty=flashcard["difficulty"],
                )
                for flashcard in flashcards
            ],
        )

        logger.info(
            "Flashcard generation completed for video %s. "
            "Generated %s flashcard(s).",
            video_id,
            len(flashcards),
        )

        return flashcards

    def process(
        self,
        job_id: int,
        video_id: int,
        file_path: str,
    ):
        """
        Execute the complete AI pipeline, stage by stage, resumably.

        Each stage's ProcessingStage row is checked before running it:
        COMPLETED is skipped (never re-executed - this is what makes
        a redelivered/retried job cheap instead of starting over from
        metadata every time); a stage whose dependency (see
        app.pipelines.stage_definitions.STAGE_DEPENDENCIES) never
        reached COMPLETED is left PENDING, never attempted (it was
        never actually tried, so it is not FAILED); everything else
        eligible is atomically claimed and run.

        A failed stage does not stop its independent siblings from
        still being attempted (summary/embedding/translation/quiz/
        chapter/flashcard all depend only on transcription, never on
        each other) - the loop continues. Only once every eligible
        stage has been attempted does this method decide whether the
        job succeeded or failed, by re-reading every stage's final
        status.
        """
        self.processing_stage_service.ensure_seeded(
            job_id,
            STAGE_ORDER,
        )

        # stage_name -> that stage's return value, FOR THIS RUN ONLY.
        # A resumed stage that was already COMPLETED in a previous
        # run never populates this dict this run - downstream stages
        # that need its output fall back to re-fetching the persisted
        # artifact (see _execute_stage) rather than assuming it is
        # here.
        results: dict[str, object] = {}
        failures: list[BaseException] = []

        for stage_name in STAGE_ORDER:
            stage_row = self.processing_stage_service.get_by_job_id_and_name(
                job_id, stage_name,
            )

            if stage_row.status == "COMPLETED":
                continue

            dependency = STAGE_DEPENDENCIES[stage_name]

            if dependency is not None:
                dependency_row = self.processing_stage_service.get_by_job_id_and_name(
                    job_id, dependency,
                )
                if dependency_row.status != "COMPLETED":
                    # Blocked, not failed: this stage was never
                    # actually attempted, so it must stay PENDING.
                    continue

            if (
                stage_row.status == "FAILED"
                and self.processing_stage_service.has_exhausted_retries(stage_row)
            ):
                logger.warning(
                    "Stage %s for job %s has exhausted its retry "
                    "budget (%s attempts); leaving it FAILED without "
                    "another attempt.",
                    stage_name, job_id, stage_row.attempt_count,
                )
                continue

            claimed = self.processing_stage_service.try_claim(
                job_id, stage_name,
            )

            if claimed is None:
                # Lost a race, or genuinely still RUNNING under a
                # still-alive attempt (not stale) - skip this pass.
                continue

            try:
                results[stage_name] = self._execute_stage(
                    stage_name=stage_name,
                    job_id=job_id,
                    video_id=video_id,
                    file_path=file_path,
                    results=results,
                )
            except Exception as exc:
                logger.exception(
                    "Stage %s failed for video %s (job %s).",
                    stage_name, video_id, job_id,
                )
                self.processing_stage_service.mark_failed(
                    claimed, str(exc),
                )
                failures.append(exc)
            else:
                self.processing_stage_service.mark_completed(
                    claimed,
                )

        final_stages = self.processing_stage_service.get_by_job_id(
            job_id,
        )
        incomplete = [
            stage.stage_name
            for stage in final_stages
            if stage.status not in ("COMPLETED", "SKIPPED")
        ]

        if incomplete:
            transient = next(
                (exc for exc in failures if is_transient_error(exc)),
                None,
            )
            if transient is not None:
                # Re-raising the original transient exception (not a
                # wrapper) so Celery's autoretry_for still recognizes
                # its type and redelivers the task - the redelivery
                # will resume at exactly the stages still incomplete.
                raise transient
            if failures:
                raise failures[0]
            raise ProcessingIncompleteError(
                f"Processing incomplete for video {video_id}: "
                f"stage(s) {incomplete} did not complete."
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

    def _execute_stage(
        self,
        stage_name: str,
        job_id: int,
        video_id: int,
        file_path: str,
        results: dict[str, object],
    ):
        """
        Dispatch to the real stage method, resolving each stage's
        real input - using this run's in-memory result when the
        dependency actually ran this run, falling back to the
        persisted artifact when it was skipped because it was already
        COMPLETED from a previous run.
        """
        if stage_name == METADATA:
            return self.metadata_stage(
                job_id=job_id, video_id=video_id, file_path=file_path,
            )

        if stage_name == TRANSCRIPTION:
            transcript, segments = self.transcription_stage(
                job_id=job_id, video_id=video_id, file_path=file_path,
            )
            results["_transcript_segments"] = segments
            return transcript

        if stage_name == CHAPTER:
            segments = results.get("_transcript_segments")

            if segments is None:
                # Resume case: transcription_stage was already
                # COMPLETED from a prior attempt, so it was skipped
                # this run and never produced segments in memory.
                # transcript_segments is the one piece of
                # transcription's output that is NOT persisted
                # anywhere (Transcript only stores flattened text -
                # see transcription_stage's own docstring), so the
                # only correct way to recover real, timestamped
                # segments is to re-run the Whisper call. Accepted
                # here as a bounded, explicit cost specific to
                # resuming chapter detection alone - it does not
                # re-run metadata/summary/embedding/translation/quiz/
                # flashcard, and save_transcript's upsert (Phase 2)
                # makes re-persisting the (should be near-identical)
                # transcript text safe either way.
                logger.warning(
                    "Re-running transcription to recover segments "
                    "for chapter detection on video %s - "
                    "transcription was already COMPLETED from a "
                    "prior attempt, so its segment output is not "
                    "available in memory this run.",
                    video_id,
                )
                rerun_result = self.transcription_worker.process(
                    video_path=file_path,
                )
                segments = rerun_result.get("segments", [])

            return self.chapter_stage(
                job_id=job_id,
                video_id=video_id,
                transcript_segments=segments,
            )

        # Every remaining stage (summary/embedding/translation/quiz/
        # flashcard) depends only on transcription's persisted
        # Transcript - reuse it from this run's results if
        # transcription actually ran this run, otherwise re-fetch the
        # persisted row (transcription was already COMPLETED earlier).
        transcript = results.get(TRANSCRIPTION)
        if transcript is None:
            transcript = self.transcript_service.get_by_video_id(
                video_id,
            )

        if stage_name == SUMMARY:
            return self.summary_stage(
                job_id=job_id, video_id=video_id, transcript=transcript,
            )
        if stage_name == EMBEDDING:
            return self.embedding_stage(
                job_id=job_id, video_id=video_id, transcript=transcript,
            )
        if stage_name == TRANSLATION:
            return self.translation_stage(
                job_id=job_id, video_id=video_id, transcript=transcript,
            )
        if stage_name == QUIZ:
            return self.quiz_stage(
                job_id=job_id, video_id=video_id, transcript=transcript,
            )
        if stage_name == FLASHCARD:
            return self.flashcard_stage(
                job_id=job_id, video_id=video_id, transcript=transcript,
            )

        raise ValueError(
            f"Unknown processing stage: {stage_name!r}"
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

        self._extract_and_save_thumbnail(
            video_id=video_id,
            file_path=file_path,
            duration=metadata.duration,
        )

    def _extract_and_save_thumbnail(
        self,
        video_id: int,
        file_path: str,
        duration: int,
    ) -> None:
        """
        Best-effort thumbnail extraction - deliberately isolated from
        metadata_stage's own exception handling (the rest of that
        stage, and the whole remaining pipeline, must run whether or
        not this succeeds). A representative frame with no library-
        page value is not worth failing a video's entire processing
        run over.
        """
        try:
            image_bytes = extract_thumbnail(file_path, duration)
            if image_bytes is None:
                return

            key = f"thumbnails/{video_id}.jpg"
            self.storage.save(key, image_bytes)
            self.video_service.update_thumbnail(
                video_id=video_id,
                thumbnail_key=key,
            )
            logger.info(
                "Thumbnail extracted and saved for video %s (key=%s)",
                video_id,
                key,
            )
        except Exception:
            logger.exception(
                "Thumbnail extraction/save failed for video %s - "
                "continuing processing without a thumbnail.",
                video_id,
            )