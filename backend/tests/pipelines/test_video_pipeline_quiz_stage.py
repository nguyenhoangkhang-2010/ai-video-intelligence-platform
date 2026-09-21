from unittest.mock import MagicMock, patch

from app.pipelines.video_pipeline import VideoPipelineService
from app.schemas.quiz import QuizCreate


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

    return pipeline, quiz_service


def test_quiz_stage_replaces_old_quizzes_before_persisting_new_ones():
    pipeline, quiz_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"

    pipeline.quiz_worker.process.return_value = [
        {
            "type": "multiple_choice",
            "question": "Q1?",
            "answer": "A",
            "options": "A,B,C,D",
        },
    ]

    manager = MagicMock()
    manager.attach_mock(quiz_service.delete_by_video_id, "delete")
    manager.attach_mock(quiz_service.create_quiz, "create")

    pipeline.quiz_stage(job_id=1, video_id=10, transcript=transcript)

    assert [entry[0] for entry in manager.mock_calls] == ["delete", "create"]
    quiz_service.delete_by_video_id.assert_called_once_with(10)

    created = quiz_service.create_quiz.call_args.args[0]
    assert isinstance(created, QuizCreate)
    assert created.video_id == 10
    assert created.question == "Q1?"
    assert created.answer == "A"
    assert created.options == "A,B,C,D"


def test_quiz_stage_deletes_old_quizzes_even_when_no_new_quizzes_generated():
    pipeline, quiz_service = _make_pipeline()

    transcript = MagicMock(name="transcript")
    transcript.text = "transcript text"

    pipeline.quiz_worker.process.return_value = []

    pipeline.quiz_stage(job_id=1, video_id=10, transcript=transcript)

    quiz_service.delete_by_video_id.assert_called_once_with(10)
    quiz_service.create_quiz.assert_not_called()
