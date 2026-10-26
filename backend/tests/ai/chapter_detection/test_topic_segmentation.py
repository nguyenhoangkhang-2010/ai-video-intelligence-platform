from unittest.mock import MagicMock

from ai.chapter_detection.topic_segmentation import TopicSegmenter
from ai.speech.speech_result import SpeechSegment


def _segments(n):
    return [
        SpeechSegment(start=float(i), end=float(i + 1), text=f"seg{i}")
        for i in range(n)
    ]


def test_segment_returns_empty_for_no_segments():
    segmenter = TopicSegmenter(embedder=MagicMock())

    assert segmenter.segment([]) == []


def test_segment_keeps_coherent_segments_together_and_detects_boundary():
    embedder = MagicMock()
    vectors = {
        "seg0": [1.0, 0.0],
        "seg1": [1.0, 0.0],
        "seg2": [1.0, 0.0],
        "seg3": [0.0, 1.0],
        "seg4": [0.0, 1.0],
    }
    embedder.embed_query.side_effect = lambda text: vectors[text]

    segmenter = TopicSegmenter(
        embedder=embedder, similarity_threshold=0.5, min_topic_segments=1,
    )

    topics = segmenter.segment(_segments(5))

    assert len(topics) == 2
    assert topics[0].segment_indices == (0, 1, 2)
    assert topics[1].segment_indices == (3, 4)
    # Chronological ordering preserved: topic 0 covers the earlier
    # segments, topic 1 the later ones.
    assert topics[0].segment_indices[-1] < topics[1].segment_indices[0]


def test_segment_produces_a_single_topic_when_everything_is_similar():
    embedder = MagicMock()
    embedder.embed_query.side_effect = lambda text: [1.0, 0.0]

    segmenter = TopicSegmenter(
        embedder=embedder, similarity_threshold=0.5, min_topic_segments=1,
    )

    topics = segmenter.segment(_segments(5))

    assert len(topics) == 1
    assert topics[0].segment_indices == (0, 1, 2, 3, 4)


def test_segment_falls_back_to_windowed_segmentation_when_no_embedder():
    segmenter = TopicSegmenter(embedder=None, min_topic_segments=2)

    topics = segmenter.segment(_segments(5))

    assert [t.segment_indices[0] for t in topics] == [0, 2, 4]


def test_segment_falls_back_when_embedding_call_raises():
    embedder = MagicMock()
    embedder.embed_query.side_effect = RuntimeError("model unavailable")

    segmenter = TopicSegmenter(embedder=embedder, min_topic_segments=2)

    topics = segmenter.segment(_segments(4))

    # Degrades gracefully - does not crash, still returns topics
    # covering every segment.
    all_indices = sorted(
        index for topic in topics for index in topic.segment_indices
    )
    assert all_indices == [0, 1, 2, 3]


def test_segment_does_not_construct_an_embedder_when_explicitly_none():
    # Regression guard for the None-vs-"not provided" ambiguity: an
    # explicit embedder=None must never fall through to constructing
    # a real (heavy) Embedder from settings.
    segmenter = TopicSegmenter(embedder=None)

    assert segmenter.embedder is None
