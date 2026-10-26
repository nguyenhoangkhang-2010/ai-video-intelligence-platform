"""
Per-segment timestamps: Whisper's timed segments are persisted with the
transcript, every retrieval chunk gets the span of video it covers, and
search results / RAG citations carry that span so the UI can seek to it.

Before this, every timestamp was dropped at the transcription stage:
the transcript was plain text, a citation couldn't say where in the
video it came from, and resuming chapter detection had to re-run
Whisper.
"""
from unittest.mock import MagicMock, patch

from ai.embedding.chunking import TextChunker
from ai.embedding.timing import chunk_time_range
from ai.retrieval.dense_retriever import DenseRetriever
from app.models.transcript import Transcript
from app.models.user import User
from app.models.video import Video
from app.pipelines.rag_pipeline import RAGPipeline
from app.pipelines.video_pipeline import VideoPipelineService, _timed_segments
from app.repositories.transcript import TranscriptRepository
from app.schemas.transcript import TranscriptCreate, TranscriptRead, TranscriptSegment
from app.services.transcript import TranscriptService


SEGMENTS = [
    {"start": 0.0, "end": 4.0, "text": "one two three"},
    {"start": 4.0, "end": 9.5, "text": "four five"},
    {"start": 9.5, "end": 15.0, "text": "six seven eight nine"},
]


# --- chunk -> time mapping ---------------------------------------------------


def test_chunk_spanning_several_segments_gets_their_combined_span():
    # words 1..5 = "two three four five six" -> segments 0..2
    assert chunk_time_range(SEGMENTS, total_words=9, word_start=1, word_end=6) == (0.0, 15.0)


def test_chunk_inside_one_segment_gets_that_segment():
    # words 3..4 = "four five" -> segment 1 only
    assert chunk_time_range(SEGMENTS, total_words=9, word_start=3, word_end=5) == (4.0, 9.5)


def test_word_count_mismatch_is_scaled_onto_the_segments():
    # Transcript text normalized to 18 words while segments hold 9:
    # the second half of the transcript maps to the second half of the segments.
    start, end = chunk_time_range(SEGMENTS, total_words=18, word_start=10, word_end=18)
    assert start >= 4.0
    assert end == 15.0


def test_no_segments_or_no_span_gives_no_time():
    assert chunk_time_range([], total_words=9, word_start=0, word_end=3) is None
    assert chunk_time_range(SEGMENTS, total_words=9, word_start=None, word_end=None) is None
    assert chunk_time_range(SEGMENTS, total_words=9, word_start=4, word_end=4) is None


def test_chunker_spans_match_its_chunks():
    chunker = TextChunker(chunk_size=4, overlap=1)
    text = "one two three four five six seven eight nine"

    spanned = chunker.chunk_with_spans(text)

    assert [chunk for chunk, _, _ in spanned] == chunker.chunk(text)
    words = text.split()
    for chunk, start, end in spanned:
        assert chunk == " ".join(words[start:end])


def test_end_to_end_chunks_from_the_real_chunker_map_to_increasing_times():
    text = " ".join(segment["text"] for segment in SEGMENTS)
    chunker = TextChunker(chunk_size=4, overlap=1)

    times = [
        chunk_time_range(SEGMENTS, len(text.split()), start, end)
        for _, start, end in chunker.chunk_with_spans(text)
    ]

    assert times[0][0] == 0.0
    assert times[-1][1] == 15.0
    assert [t[0] for t in times] == sorted(t[0] for t in times)


# --- persistence -------------------------------------------------------------


def _video(db_session) -> Video:
    user = User(username="owner", email="owner@example.com", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    video = Video(owner_id=user.id, title="clip", filename="clip.mp4", language="vi", duration=15, status="processing")
    db_session.add(video)
    db_session.commit()
    return video


def test_transcript_segments_are_saved_and_returned_by_the_read_schema(db_session):
    video = _video(db_session)
    service = TranscriptService(TranscriptRepository(db_session))

    saved = service.save_transcript(
        TranscriptCreate(
            video_id=video.id,
            language="vi",
            text="one two three four five",
            segments=[TranscriptSegment(**SEGMENTS[0]), TranscriptSegment(**SEGMENTS[1])],
        )
    )

    db_session.expire_all()
    reloaded = db_session.get(Transcript, saved.id)
    assert reloaded.segments == [
        {"start": 0.0, "end": 4.0, "text": "one two three"},
        {"start": 4.0, "end": 9.5, "text": "four five"},
    ]
    read = TranscriptRead.model_validate(reloaded)
    assert read.segments[1].start == 4.0


def test_reprocessing_replaces_segments(db_session):
    video = _video(db_session)
    service = TranscriptService(TranscriptRepository(db_session))
    service.save_transcript(
        TranscriptCreate(video_id=video.id, language="vi", text="old", segments=[TranscriptSegment(**SEGMENTS[0])])
    )

    updated = service.save_transcript(TranscriptCreate(video_id=video.id, language="vi", text="new text"))

    assert updated.segments is None


def test_timed_segments_keeps_timing_and_text_and_drops_unusable_rows():
    raw = [
        {"start": 0.0, "end": 1.5, "text": " hello ", "no_speech_prob": 0.01, "speaker": None},
        {"start": 2.0, "end": 1.0, "text": "end before start"},
        {"end": 3.0, "text": "no start"},
        {"start": 3.0, "end": 4.0, "text": "bye", "speaker": "SPEAKER_00"},
    ]

    timed = _timed_segments(raw)

    assert [(s.start, s.end, s.text, s.speaker) for s in timed] == [
        (0.0, 1.5, "hello", None),
        (3.0, 4.0, "bye", "SPEAKER_00"),
    ]


# --- pipeline wiring ---------------------------------------------------------


def _pipeline():
    services = {
        name: MagicMock(name=name)
        for name in (
            "video_service", "transcript_service", "summary_service", "embedding_service",
            "translation_service", "processing_job_service", "processing_stage_service",
            "quiz_service", "chapter_service", "flashcard_service", "storage",
        )
    }
    with (
        patch("app.pipelines.video_pipeline.TranscriptionWorker"),
        patch("app.pipelines.video_pipeline.SummaryWorker"),
        patch("app.pipelines.video_pipeline.EmbeddingWorker"),
        patch("app.pipelines.video_pipeline.TranslationWorker"),
        patch("app.pipelines.video_pipeline.QuizWorker"),
        patch("app.pipelines.video_pipeline.ChapterTopicPipeline"),
        patch("app.pipelines.video_pipeline.FlashcardWorker"),
    ):
        return VideoPipelineService(**services), services


def test_transcription_stage_persists_timed_segments():
    pipeline, services = _pipeline()
    pipeline.transcription_worker.process.return_value = {
        "language": "vi",
        "text": "one two three four five",
        "segments": SEGMENTS[:2],
    }

    pipeline.transcription_stage(job_id=1, video_id=7, file_path="/tmp/v.mp4")

    saved = services["transcript_service"].save_transcript.call_args.args[0]
    assert [(s.start, s.end) for s in saved.segments] == [(0.0, 4.0), (4.0, 9.5)]


def test_embedding_stage_stores_each_chunks_time_span():
    pipeline, services = _pipeline()
    transcript = MagicMock(name="transcript")
    transcript.text = "one two three four five six seven eight nine"
    transcript.segments = SEGMENTS
    pipeline.embedding_worker.process.return_value = [
        {"vector": [0.1], "vector_id": "v0", "chunk_index": 0, "chunk_text": "one two three four",
         "embedding_model": "m", "word_start": 0, "word_end": 4},
        {"vector": [0.2], "vector_id": "v1", "chunk_index": 1, "chunk_text": "six seven eight nine",
         "embedding_model": "m", "word_start": 5, "word_end": 9},
    ]
    services["embedding_service"].get_by_video_id.return_value = []

    with patch("app.pipelines.video_pipeline.VectorStore"):
        pipeline.embedding_stage(job_id=1, video_id=7, transcript=transcript)

    rows = services["embedding_service"].replace_for_video.call_args.args[1]
    assert (rows[0].start_time, rows[0].end_time) == (0.0, 9.5)
    assert (rows[1].start_time, rows[1].end_time) == (9.5, 15.0)


def test_embedding_stage_without_segments_stores_no_times():
    pipeline, services = _pipeline()
    transcript = MagicMock(name="transcript")
    transcript.text = "one two"
    transcript.segments = None
    pipeline.embedding_worker.process.return_value = [
        {"vector": [0.1], "vector_id": "v0", "chunk_index": 0, "chunk_text": "one two",
         "embedding_model": "m", "word_start": 0, "word_end": 2},
    ]
    services["embedding_service"].get_by_video_id.return_value = []

    with patch("app.pipelines.video_pipeline.VectorStore"):
        pipeline.embedding_stage(job_id=1, video_id=7, transcript=transcript)

    row = services["embedding_service"].replace_for_video.call_args.args[1][0]
    assert row.start_time is None and row.end_time is None


# --- search results and citations carry the span -----------------------------


def test_dense_retrieval_and_rag_sources_carry_chunk_times():
    semantic = MagicMock(name="semantic_search_service")
    semantic.search.return_value = [
        {"vector_id": "v1", "video_id": 7, "chunk_index": 1, "chunk_text": "four five",
         "distance": 0.2, "start_time": 4.0, "end_time": 9.5},
    ]
    embedding_service = MagicMock(name="embedding_service")
    embedding_service.get_by_video_id.return_value = [object()]
    answerer = MagicMock(name="answerer")
    answerer.answer.return_value = "Năm."

    pipeline = RAGPipeline(
        semantic_search_service=semantic,
        embedding_service=embedding_service,
        answerer=answerer,
        retriever=DenseRetriever(semantic_search_service=semantic),
    )
    result = pipeline.ask(video_id=7, query="số năm?")

    assert result.status == "answered"
    assert (result.sources[0].start_time, result.sources[0].end_time) == (4.0, 9.5)


def test_resumed_chapter_stage_uses_persisted_segments_instead_of_rerunning_whisper():
    pipeline, services = _pipeline()
    persisted = MagicMock(name="transcript")
    persisted.segments = SEGMENTS
    services["transcript_service"].get_by_video_id.return_value = persisted

    with patch.object(pipeline, "chapter_stage") as chapter_stage:
        pipeline._execute_stage("chapter", job_id=1, video_id=7, file_path="/tmp/v.mp4", results={})

    pipeline.transcription_worker.process.assert_not_called()
    assert chapter_stage.call_args.kwargs["transcript_segments"] == SEGMENTS


def test_resumed_chapter_stage_falls_back_to_whisper_for_an_old_transcript():
    pipeline, services = _pipeline()
    persisted = MagicMock(name="transcript")
    persisted.segments = None
    services["transcript_service"].get_by_video_id.return_value = persisted
    pipeline.transcription_worker.process.return_value = {"segments": SEGMENTS}

    with patch.object(pipeline, "chapter_stage") as chapter_stage:
        pipeline._execute_stage("chapter", job_id=1, video_id=7, file_path="/tmp/v.mp4", results={})

    pipeline.transcription_worker.process.assert_called_once()
    assert chapter_stage.call_args.kwargs["transcript_segments"] == SEGMENTS
