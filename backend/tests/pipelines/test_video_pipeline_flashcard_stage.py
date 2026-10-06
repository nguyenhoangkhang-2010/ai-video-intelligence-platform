from unittest.mock import MagicMock, patch

from app.pipelines.video_pipeline import VideoPipelineService
from app.schemas.flashcard import FlashcardCreate


def _make_pipeline():
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")
    summary_service = MagicMock(name="summary_service")
    embedding_service = MagicMock(name="embedding_service")
    translation_service = MagicMock(name="translation_service")
    processing_job_service = MagicMock(name="processing_job_service")
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
            quiz_service=quiz_service,
            chapter_service=chapter_service,
            flashcard_service=flashcard_service,
            storage=storage,
        )

    return pipeline, flashcard_service


def test_flashcard_stage_atomically_replaces_old_flashcards_with_new_ones():
    pipeline, flashcard_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"

    pipeline.flashcard_worker.process.return_value = [
        {"question": "Front?", "answer": "Back.", "difficulty": "medium"},
    ]

    pipeline.flashcard_stage(job_id=1, video_id=10, transcript=transcript)

    # Idempotent by atomic replacement, not delete-then-per-row-create:
    # replace_for_video is called exactly once with the complete new
    # artifact set (see FlashcardRepository.replace_for_video).
    flashcard_service.replace_for_video.assert_called_once()
    call_args = flashcard_service.replace_for_video.call_args.args
    assert call_args[0] == 10

    created = call_args[1]
    assert len(created) == 1
    assert isinstance(created[0], FlashcardCreate)
    assert created[0].video_id == 10
    assert created[0].question == "Front?"
    assert created[0].answer == "Back."
    assert created[0].difficulty == "medium"


def test_flashcard_stage_replaces_with_empty_set_when_none_generated():
    pipeline, flashcard_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"

    pipeline.flashcard_worker.process.return_value = []

    pipeline.flashcard_stage(job_id=1, video_id=10, transcript=transcript)

    # Still calls replace_for_video (with an empty list) rather than a
    # bare delete - this atomically clears any stale flashcards from a
    # previous attempt even when nothing new was generated.
    flashcard_service.replace_for_video.assert_called_once_with(10, [])
