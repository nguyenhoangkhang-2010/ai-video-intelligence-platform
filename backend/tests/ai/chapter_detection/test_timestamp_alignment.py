from ai.chapter_detection.chapter_result import Chapter, Topic
from ai.chapter_detection.timestamp_alignment import (
    align_chapters,
    align_topics,
    resolve_boundary,
)
from ai.speech.speech_result import SpeechSegment


def _segments():
    return [
        SpeechSegment(start=0.0, end=1.0, text="a", speaker="Speaker 1"),
        SpeechSegment(start=1.0, end=2.5, text="b", speaker="Speaker 1"),
        SpeechSegment(start=2.5, end=4.0, text="c", speaker="Speaker 2"),
    ]


def test_resolve_boundary_returns_min_start_and_max_end():
    start, end, speaker = resolve_boundary((0, 1), _segments())

    assert start == 0.0
    assert end == 2.5
    assert speaker == "Speaker 1"


def test_resolve_boundary_handles_empty_indices_safely():
    start, end, speaker = resolve_boundary((), _segments())

    assert start is None
    assert end is None
    assert speaker is None


def test_resolve_boundary_ignores_out_of_range_indices_safely():
    start, end, speaker = resolve_boundary((0, 99), _segments())

    # Only the valid index (0) contributes - never raises for an
    # invalid/missing reference.
    assert start == 0.0
    assert end == 1.0
    assert speaker == "Speaker 1"


def test_resolve_boundary_returns_none_when_all_indices_invalid():
    start, end, speaker = resolve_boundary((99, 100), _segments())

    assert (start, end, speaker) == (None, None, None)


def test_resolve_boundary_picks_dominant_speaker_by_segment_count():
    # Segment 2 (Speaker 2) has 1 segment; segments 0+1 (Speaker 1)
    # have 2 - Speaker 1 should win.
    start, end, speaker = resolve_boundary((0, 1, 2), _segments())

    assert speaker == "Speaker 1"


def test_align_topics_fills_in_start_end_and_dominant_speaker():
    topics = [Topic(id="t0", label="Topic 1", segment_indices=(0, 1))]

    aligned = align_topics(topics, _segments())

    assert aligned[0].start == 0.0
    assert aligned[0].end == 2.5
    assert aligned[0].metadata["dominant_speaker"] == "Speaker 1"
    # Original identity/label untouched.
    assert aligned[0].id == "t0"
    assert aligned[0].label == "Topic 1"


def test_align_chapters_fills_in_start_end_and_dominant_speaker():
    chapters = [
        Chapter(
            id="c0", title="Chapter 1", topics=(),
            segment_indices=(1, 2),
        ),
    ]

    aligned = align_chapters(chapters, _segments())

    assert aligned[0].start == 1.0
    assert aligned[0].end == 4.0


def test_align_topics_never_invents_timestamps_for_empty_indices():
    topics = [Topic(id="t0", label="Topic 1", segment_indices=())]

    aligned = align_topics(topics, _segments())

    assert aligned[0].start is None
    assert aligned[0].end is None
