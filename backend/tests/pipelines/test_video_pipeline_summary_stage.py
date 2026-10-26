from unittest.mock import MagicMock, patch

import pytest

from ai.llm.errors import LLMConnectionError
from app.pipelines.video_pipeline import VideoPipelineService
from app.schemas.summary import SummaryCreate


def _make_pipeline():
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")
    summary_service = MagicMock(name="summary_service")
    embedding_service = MagicMock(name="embedding_service")
    translation_service = MagicMock(name="translation_service")
    processing_job_service = MagicMock(name="processing_job_service")
    processing_stage_service = MagicMock(name="processing_stage_service")
    quiz_service = MagicMock(name="quiz_service")
    chapter_service = MagicMock(name="chapter_service")
    flashcard_service = MagicMock(name="flashcard_service")
    storage = MagicMock(name="storage")

    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
        patch("app.pipelines.video_pipeline.ChapterTopicPipeline"),
        patch("app.pipelines.video_pipeline.FlashcardWorker"),
    ):
        pipeline = VideoPipelineService(
            video_service=video_service,
            transcript_service=transcript_service,
            summary_service=summary_service,
            embedding_service=embedding_service,
            translation_service=translation_service,
            processing_job_service=processing_job_service,
            processing_stage_service=processing_stage_service,
            quiz_service=quiz_service,
            chapter_service=chapter_service,
            flashcard_service=flashcard_service,
            storage=storage,
        )

    return pipeline, summary_service, processing_job_service


def test_summary_stage_persists_the_real_generated_content():
    pipeline, summary_service, _ = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"

    pipeline.summary_worker.process.return_value = {
        "type": "default",
        "content": "Nội dung chính: vượt qua nỗi sợ.",
        "model_name": "qwen3:8b",
    }

    pipeline.summary_stage(job_id=1, video_id=10, transcript=transcript)

    pipeline.summary_worker.process.assert_called_once_with(transcript="transcript text")

    # save_summary (an upsert), not create_summary - a reprocessed
    # video must get a genuinely regenerated summary, never silently
    # keep a prior attempt's content.
    summary_service.save_summary.assert_called_once()
    created = summary_service.save_summary.call_args.args[0]
    assert isinstance(created, SummaryCreate)
    assert created.video_id == 10
    assert created.type == "default"
    assert created.content == "Nội dung chính: vượt qua nỗi sợ."
    assert created.model_name == "qwen3:8b"


def test_summary_stage_reports_progress_before_generating():
    pipeline, _, processing_job_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"
    pipeline.summary_worker.process.return_value = {
        "type": "default", "content": "x", "model_name": "qwen3:8b",
    }

    pipeline.summary_stage(job_id=1, video_id=10, transcript=transcript)

    processing_job_service.update_progress.assert_called_once_with(
        job_id=1, progress=95, current_step="Generating Summary",
    )


def test_summary_stage_never_persists_anything_when_generation_fails():
    """
    No false-success state: if the LLM call fails, save_summary must
    never be called - a failed generation can never be silently
    recorded as a real summary a user would see.
    """
    pipeline, summary_service, _ = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"
    pipeline.summary_worker.process.side_effect = LLMConnectionError("unreachable")

    with pytest.raises(LLMConnectionError):
        pipeline.summary_stage(job_id=1, video_id=10, transcript=transcript)

    summary_service.save_summary.assert_not_called()
