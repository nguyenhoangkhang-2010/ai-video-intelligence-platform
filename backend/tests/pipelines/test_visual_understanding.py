"""
The visual stage and how speech and visuals meet in the pipeline:
- a video with no speech gets its transcript from what is on screen
  instead of failing;
- visual segments become their own, labelled retrieval chunks, with
  their similarity to what was said stored for the UI;
- the visual stage never fails a video's processing.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from ai.speech.pipeline import NoSpeechDetectedError
from app.pipelines.video_pipeline import VideoPipelineService


def _make_pipeline(visual_rows=()):
    services = {
        name: MagicMock(name=name)
        for name in (
            "video_service", "transcript_service", "summary_service", "embedding_service",
            "translation_service", "processing_job_service", "processing_stage_service",
            "quiz_service", "chapter_service", "flashcard_service", "storage",
        )
    }
    visual_service = MagicMock(name="visual_segment_service")
    visual_service.get_by_video_id.return_value = list(visual_rows)

    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
        patch("app.pipelines.video_pipeline.ChapterTopicPipeline"),
        patch("app.pipelines.video_pipeline.FlashcardWorker"),
    ):
        pipeline = VideoPipelineService(**services, visual_segment_service=visual_service)

    services["transcript_service"].save_transcript.side_effect = lambda data: data
    return pipeline, services, visual_service


def _row(id, start, end, text="", description=""):
    return SimpleNamespace(id=id, start_time=start, end_time=end, on_screen_text=text, description=description)


# ---- no speech -> transcript from the screen ----

def test_video_without_speech_gets_a_transcript_from_the_screen():
    pipeline, services, _ = _make_pipeline([
        _row(1, 0, 12, "Bước 1: Mở cài đặt", "Ảnh chụp màn hình điện thoại."),
        _row(2, 12, 30, "", ""),  # nothing readable: left out
    ])
    pipeline.transcription_worker.process.side_effect = NoSpeechDetectedError("No speech detected in audio.")

    with patch("app.pipelines.video_pipeline.has_audio_stream", return_value=True):
        transcript, segments = pipeline.transcription_stage(job_id=1, video_id=7, file_path="v.mp4")

    assert transcript.source == "visual"
    assert transcript.language == "vi"
    assert transcript.text == "Chữ trên màn hình: Bước 1: Mở cài đặt\nHình ảnh: Ảnh chụp màn hình điện thoại."
    assert [(s.start, s.end) for s in transcript.segments] == [(0, 12)]
    assert segments == [{"start": 0, "end": 12, "text": transcript.text}]


def test_video_without_an_audio_stream_skips_whisper():
    pipeline, _, _ = _make_pipeline([_row(1, 0, 5, "Hello world")])

    with patch("app.pipelines.video_pipeline.has_audio_stream", return_value=False):
        transcript, _ = pipeline.transcription_stage(job_id=1, video_id=7, file_path="v.mp4")

    pipeline.transcription_worker.process.assert_not_called()
    assert transcript.source == "visual"
    assert transcript.language == "en"


def test_no_speech_and_nothing_on_screen_still_fails():
    pipeline, _, _ = _make_pipeline([])
    pipeline.transcription_worker.process.return_value = {"text": "   ", "language": "vi", "segments": []}

    with patch("app.pipelines.video_pipeline.has_audio_stream", return_value=True):
        with pytest.raises(ValueError, match="No speech detected"):
            pipeline.transcription_stage(job_id=1, video_id=7, file_path="v.mp4")


# ---- visual chunks in the search index ----

def _speech_transcript():
    return SimpleNamespace(
        text="doanh thu tăng hai mươi phần trăm",
        source="speech",
        segments=[{"start": 0.0, "end": 10.0, "text": "doanh thu tăng hai mươi phần trăm"}],
    )


def _speech_embedding():
    return {
        "vector": [0.1], "vector_id": "s-0", "chunk_index": 0,
        "chunk_text": "doanh thu tăng hai mươi phần trăm", "embedding_model": "m",
        "word_start": 0, "word_end": 7,
    }


def test_visual_segments_are_embedded_as_labelled_chunks_with_speech_similarity():
    pipeline, services, visual_service = _make_pipeline([_row(5, 2, 9, "Doanh thu +20%", "Biểu đồ cột.")])
    services["embedding_service"].get_by_video_id.return_value = []
    pipeline.embedding_worker.process.return_value = [_speech_embedding()]
    pipeline.embedding_worker.process_texts.return_value = [
        {"vector": [0.2], "vector_id": "v-1", "chunk_index": 1,
         "chunk_text": "Chữ trên màn hình: Doanh thu +20%\nHình ảnh: Biểu đồ cột.", "embedding_model": "m"},
    ]
    pipeline.embedding_worker.similarity.return_value = 0.71

    with patch("app.pipelines.video_pipeline.VectorStore"):
        pipeline.embedding_stage(job_id=1, video_id=7, transcript=_speech_transcript())

    pipeline.embedding_worker.process_texts.assert_called_once()
    assert pipeline.embedding_worker.process_texts.call_args.kwargs["start_index"] == 1
    rows = services["embedding_service"].replace_for_video.call_args.args[1]
    assert [(row.source, row.start_time, row.end_time) for row in rows] == [
        ("speech", 0.0, 10.0),
        ("visual", 2, 9),
    ]
    # Compared with what was said while it was on screen.
    assert pipeline.embedding_worker.similarity.call_args.args[1] == "doanh thu tăng hai mươi phần trăm"
    visual_service.set_speech_similarity.assert_called_once_with({5: 0.71})


def test_visual_transcript_is_not_embedded_twice():
    pipeline, services, _ = _make_pipeline([_row(5, 0, 9, "Slide")])
    services["embedding_service"].get_by_video_id.return_value = []
    pipeline.embedding_worker.process.return_value = [_speech_embedding()]
    transcript = SimpleNamespace(text="Chữ trên màn hình: Slide", source="visual", segments=[])

    with patch("app.pipelines.video_pipeline.VectorStore"):
        pipeline.embedding_stage(job_id=1, video_id=7, transcript=transcript)

    pipeline.embedding_worker.process_texts.assert_not_called()
    rows = services["embedding_service"].replace_for_video.call_args.args[1]
    assert [row.source for row in rows] == ["visual"]


def test_a_visual_embedding_failure_keeps_the_transcript_chunks():
    pipeline, services, _ = _make_pipeline([_row(5, 2, 9, "Slide")])
    services["embedding_service"].get_by_video_id.return_value = []
    pipeline.embedding_worker.process.return_value = [_speech_embedding()]
    pipeline.embedding_worker.process_texts.side_effect = RuntimeError("encoder crashed")

    with patch("app.pipelines.video_pipeline.VectorStore"):
        pipeline.embedding_stage(job_id=1, video_id=7, transcript=_speech_transcript())

    rows = services["embedding_service"].replace_for_video.call_args.args[1]
    assert [row.source for row in rows] == ["speech"]


# ---- the visual stage is best-effort ----

def test_visual_stage_never_fails_processing():
    pipeline, _, visual_service = _make_pipeline()

    with patch.object(pipeline, "_analyse_visuals", side_effect=RuntimeError("ffmpeg exploded")):
        assert pipeline.visual_stage(job_id=1, video_id=7, file_path="v.mp4") == []

    visual_service.replace_for_video.assert_not_called()


def test_visual_stage_can_be_disabled(monkeypatch):
    pipeline, _, _ = _make_pipeline()
    monkeypatch.setattr("app.pipelines.video_pipeline.settings.vision.enabled", False)

    with patch.object(pipeline, "_analyse_visuals") as analyse:
        assert pipeline.visual_stage(job_id=1, video_id=7, file_path="v.mp4") == []

    analyse.assert_not_called()


def test_visual_stage_saves_merged_segments_and_frames(tmp_path):
    from ai.vision.describer import FrameDescription

    pipeline, services, visual_service = _make_pipeline()
    frame = tmp_path / "000.jpg"
    frame.write_bytes(b"jpeg")
    described = [
        FrameDescription(0.5, str(frame), "Slide 1", "a"),
        FrameDescription(10.0, str(frame), "Slide 1", "a"),
    ]
    visual_service.replace_for_video.side_effect = lambda video_id, rows: rows

    with (
        patch("app.pipelines.video_pipeline.extract_metadata", return_value=SimpleNamespace(duration=20)),
        patch("app.pipelines.video_pipeline.extract_keyframes", return_value=["frames"]),
        patch("app.pipelines.video_pipeline.FrameDescriber") as describer,
    ):
        describer.return_value.describe.return_value = described
        saved = pipeline.visual_stage(job_id=1, video_id=7, file_path="v.mp4")

    assert [(s.start_time, s.end_time, s.on_screen_text, s.frame_key) for s in saved] == [
        (0.5, 20.0, "Slide 1", "frames/7/000.jpg"),
    ]
    services["storage"].save.assert_called_once_with("frames/7/000.jpg", b"jpeg")
