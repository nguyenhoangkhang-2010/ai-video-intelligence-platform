from unittest.mock import MagicMock

from ai.chapter_detection.chapter_detector import ChapterDetector
from ai.chapter_detection.chapter_result import Topic
from ai.speech.speech_result import SpeechSegment


def _segments():
    return [
        SpeechSegment(start=0.0, end=1.0, text="alpha"),
        SpeechSegment(start=1.0, end=2.0, text="beta"),
        SpeechSegment(start=2.0, end=3.0, text="gamma"),
    ]


def _topics():
    return [
        Topic(id="topic-0", label="Topic 1", segment_indices=(0,)),
        Topic(id="topic-1", label="Topic 2", segment_indices=(1,)),
        Topic(id="topic-2", label="Topic 3", segment_indices=(2,)),
    ]


def test_detect_returns_empty_for_no_topics():
    detector = ChapterDetector(embedder=MagicMock(), labeler=MagicMock())

    assert detector.detect([], _segments()) == []


def test_detect_groups_similar_adjacent_topics_into_one_chapter():
    embedder = MagicMock()
    vectors = {"alpha": [1.0, 0.0], "beta": [1.0, 0.0], "gamma": [0.0, 1.0]}
    embedder.embed_query.side_effect = lambda text: vectors[text]

    labeler = MagicMock()
    labeler.label.return_value = "A Chapter"

    detector = ChapterDetector(
        embedder=embedder, labeler=labeler,
        similarity_threshold=0.5, max_topics_per_chapter=10,
    )

    chapters = detector.detect(_topics(), _segments())

    assert len(chapters) == 2
    assert chapters[0].segment_indices == (0, 1)
    assert chapters[1].segment_indices == (2,)
    assert len(chapters[0].topics) == 2
    assert len(chapters[1].topics) == 1


def test_detect_never_produces_overlapping_chapters():
    embedder = MagicMock()
    embedder.embed_query.side_effect = lambda text: [1.0, 0.0]
    labeler = MagicMock()
    labeler.label.return_value = "Chapter"

    detector = ChapterDetector(
        embedder=embedder, labeler=labeler, max_topics_per_chapter=1,
    )

    chapters = detector.detect(_topics(), _segments())

    all_indices = [
        index
        for chapter in chapters
        for index in chapter.segment_indices
    ]
    assert sorted(all_indices) == all_indices
    assert len(set(all_indices)) == len(all_indices)


def test_detect_respects_max_topics_per_chapter():
    embedder = MagicMock()
    embedder.embed_query.side_effect = lambda text: [1.0, 0.0]  # all similar
    labeler = MagicMock()
    labeler.label.return_value = "Chapter"

    detector = ChapterDetector(
        embedder=embedder, labeler=labeler,
        similarity_threshold=0.5, max_topics_per_chapter=2,
    )

    chapters = detector.detect(_topics(), _segments())

    assert all(len(chapter.topics) <= 2 for chapter in chapters)


def test_detect_uses_labeler_for_chapter_titles():
    embedder = MagicMock()
    embedder.embed_query.side_effect = lambda text: [1.0, 0.0]
    labeler = MagicMock()
    labeler.label.return_value = "Generated Title"

    detector = ChapterDetector(embedder=embedder, labeler=labeler)

    chapters = detector.detect(_topics()[:1], _segments())

    assert chapters[0].title == "Generated Title"
    labeler.label.assert_called_once_with("alpha")


def test_detect_falls_back_to_snippet_title_when_no_labeler():
    detector = ChapterDetector(
        embedder=None, labeler=None, max_topics_per_chapter=10,
    )

    chapters = detector.detect(_topics(), _segments())

    # Generic, non-hardcoded fallback derived from the actual text.
    assert chapters[0].title != ""
    assert "alpha" in chapters[0].title or "beta" in chapters[0].title


def test_detect_falls_back_to_windowed_grouping_when_no_embedder():
    detector = ChapterDetector(
        embedder=None, labeler=MagicMock(), max_topics_per_chapter=2,
    )
    detector.labeler.label.return_value = "Chapter"

    chapters = detector.detect(_topics(), _segments())

    assert len(chapters) == 2
    assert chapters[0].segment_indices == (0, 1)
    assert chapters[1].segment_indices == (2,)
