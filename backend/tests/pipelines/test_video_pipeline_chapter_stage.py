from unittest.mock import MagicMock, patch

from ai.chapter_detection.chapter_result import Chapter, ChapterResult
from app.pipelines.video_pipeline import VideoPipelineService
from app.schemas.chapter import ChapterCreate


def _make_pipeline():
    video_service = MagicMock(name="video_service")
    transcript_service = MagicMock(name="transcript_service")
    summary_service = MagicMock(name="summary_service")
    embedding_service = MagicMock(name="embedding_service")
    translation_service = MagicMock(name="translation_service")
    processing_job_service = MagicMock(name="processing_job_service")
    quiz_service = MagicMock(name="quiz_service")
    chapter_service = MagicMock(name="chapter_service")

    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
        patch("app.pipelines.video_pipeline.ChapterTopicPipeline"),
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
        )

    return pipeline, chapter_service


def test_chapter_stage_converts_segments_and_persists_new_chapters():
    pipeline, chapter_service = _make_pipeline()

    chapters = (
        Chapter(
            id="c0", title="Intro", topics=(), segment_indices=(0,),
            start=0.0, end=5.0, summary="A brief intro",
        ),
    )
    pipeline.chapter_pipeline.run.return_value = ChapterResult(
        video_id=10, chapters=chapters,
    )

    transcript_segments = [
        {"start": 0.0, "end": 5.0, "text": "hello", "speaker": "Speaker 1"},
    ]

    result = pipeline.chapter_stage(
        job_id=1, video_id=10, transcript_segments=transcript_segments,
    )

    # Dict segments from transcription are converted into SpeechSegment
    # and passed through to the chapter/topic pipeline.
    run_kwargs = pipeline.chapter_pipeline.run.call_args.kwargs
    assert run_kwargs["video_id"] == 10
    assert len(run_kwargs["segments"]) == 1
    assert run_kwargs["segments"][0].text == "hello"
    assert run_kwargs["segments"][0].speaker == "Speaker 1"

    created = chapter_service.create_chapter.call_args.args[0]
    assert isinstance(created, ChapterCreate)
    assert created.video_id == 10
    assert created.title == "Intro"
    assert created.start_time == 0.0
    assert created.end_time == 5.0
    assert created.summary == "A brief intro"

    assert result == chapters


def test_chapter_stage_replaces_old_chapters_before_persisting_new_ones():
    pipeline, chapter_service = _make_pipeline()

    chapters = (
        Chapter(
            id="c0", title="A", topics=(), segment_indices=(0,),
            start=0.0, end=1.0,
        ),
    )
    pipeline.chapter_pipeline.run.return_value = ChapterResult(
        video_id=10, chapters=chapters,
    )

    manager = MagicMock()
    manager.attach_mock(chapter_service.delete_by_video_id, "delete")
    manager.attach_mock(chapter_service.create_chapter, "create")

    pipeline.chapter_stage(
        job_id=1, video_id=10,
        transcript_segments=[{"start": 0.0, "end": 1.0, "text": "x"}],
    )

    assert [entry[0] for entry in manager.mock_calls] == ["delete", "create"]
    chapter_service.delete_by_video_id.assert_called_once_with(10)


def test_chapter_stage_persists_nothing_extra_when_no_chapters_detected():
    pipeline, chapter_service = _make_pipeline()

    pipeline.chapter_pipeline.run.return_value = ChapterResult(
        video_id=10, chapters=(),
    )

    result = pipeline.chapter_stage(
        job_id=1, video_id=10, transcript_segments=[],
    )

    chapter_service.delete_by_video_id.assert_called_once_with(10)
    chapter_service.create_chapter.assert_not_called()
    assert result == ()


def test_chapter_stage_does_not_raise_when_chapter_pipeline_finds_nothing():
    # A degenerate/empty transcript is a valid, non-error outcome for
    # chapter detection - this stage must not fail the whole
    # processing job just because no chapters were found.
    pipeline, chapter_service = _make_pipeline()

    pipeline.chapter_pipeline.run.return_value = ChapterResult(
        video_id=10, chapters=(),
    )

    pipeline.chapter_stage(job_id=1, video_id=10, transcript_segments=[])
