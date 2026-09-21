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
        )

    return pipeline, flashcard_service


def test_flashcard_stage_replaces_old_flashcards_before_persisting_new_ones():
    pipeline, flashcard_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"

    pipeline.flashcard_worker.process.return_value = [
        {"question": "Front?", "answer": "Back.", "difficulty": "medium"},
    ]

    manager = MagicMock()
    manager.attach_mock(flashcard_service.delete_by_video_id, "delete")
    manager.attach_mock(flashcard_service.create_flashcard, "create")

    pipeline.flashcard_stage(job_id=1, video_id=10, transcript=transcript)

    assert [entry[0] for entry in manager.mock_calls] == ["delete", "create"]
    flashcard_service.delete_by_video_id.assert_called_once_with(10)

    created = flashcard_service.create_flashcard.call_args.args[0]
    assert isinstance(created, FlashcardCreate)
    assert created.video_id == 10
    assert created.question == "Front?"
    assert created.answer == "Back."
    assert created.difficulty == "medium"


def test_flashcard_stage_deletes_old_flashcards_even_when_none_generated():
    pipeline, flashcard_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"

    pipeline.flashcard_worker.process.return_value = []

    pipeline.flashcard_stage(job_id=1, video_id=10, transcript=transcript)

    flashcard_service.delete_by_video_id.assert_called_once_with(10)
    flashcard_service.create_flashcard.assert_not_called()
