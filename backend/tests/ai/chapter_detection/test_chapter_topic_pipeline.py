from unittest.mock import MagicMock

from ai.chapter_detection.chapter_result import Chapter, ChapterResult, Topic
from ai.chapter_detection.pipeline import ChapterTopicPipeline
from ai.speech.speech_result import SpeechSegment


def _segments():
    return [
        SpeechSegment(start=0.0, end=1.0, text="alpha"),
        SpeechSegment(start=1.0, end=2.0, text="beta"),
    ]


def test_run_returns_empty_result_for_no_segments():
    pipeline = ChapterTopicPipeline(
        topic_segmenter=MagicMock(),
        chapter_detector=MagicMock(),
        post_processor=MagicMock(),
    )

    result = pipeline.run(segments=[], video_id=10)

    assert result == ChapterResult(video_id=10, chapters=())


def test_run_orchestrates_segmentation_detection_alignment_and_postprocessing():
    topic_segmenter = MagicMock(name="topic_segmenter")
    chapter_detector = MagicMock(name="chapter_detector")
    post_processor = MagicMock(name="post_processor")

    topics = [Topic(id="t0", label="Topic 1", segment_indices=(0, 1))]
    topic_segmenter.segment.return_value = topics

    chapters = [
        Chapter(
            id="c0", title="Chapter 1", topics=tuple(topics),
            segment_indices=(0, 1),
        ),
    ]
    chapter_detector.detect.return_value = chapters

    final_chapters = [
        Chapter(
            id="c0", title="Chapter 1", topics=tuple(topics),
            segment_indices=(0, 1), start=0.0, end=2.0,
        ),
    ]
    post_processor.process.return_value = final_chapters

    pipeline = ChapterTopicPipeline(
        topic_segmenter=topic_segmenter,
        chapter_detector=chapter_detector,
        post_processor=post_processor,
    )

    result = pipeline.run(segments=_segments(), video_id=42)

    topic_segmenter.segment.assert_called_once_with(_segments())
    chapter_detector.detect.assert_called_once()
    # detect() receives the (aligned) topics and the original segments.
    detect_args = chapter_detector.detect.call_args.args
    assert [t.id for t in detect_args[0]] == ["t0"]
    # Alignment ran before detect(): topics passed to detect() have
    # start/end resolved, not left as None.
    assert detect_args[0][0].start == 0.0
    assert detect_args[0][0].end == 2.0

    post_processor.process.assert_called_once()

    assert result.video_id == 42
    assert result.chapters == tuple(final_chapters)


def test_run_produces_a_real_end_to_end_chapter_result_without_mocks():
    # No embedder/labeler -> deterministic fallback paths throughout,
    # no real model/network involved, but exercises the real
    # TopicSegmenter/ChapterDetector/alignment/post-processing logic
    # together.
    from ai.chapter_detection.chapter_detector import ChapterDetector
    from ai.chapter_detection.chapter_postprocess import ChapterPostProcessor
    from ai.chapter_detection.topic_segmentation import TopicSegmenter

    pipeline = ChapterTopicPipeline(
        topic_segmenter=TopicSegmenter(embedder=None, min_topic_segments=1),
        chapter_detector=ChapterDetector(
            embedder=None, labeler=None, max_topics_per_chapter=10,
        ),
        post_processor=ChapterPostProcessor(min_chapter_duration_seconds=0.0),
    )

    segments = [
        SpeechSegment(start=0.0, end=5.0, text="Introduction remarks here"),
        SpeechSegment(start=5.0, end=10.0, text="More discussion continues"),
    ]

    result = pipeline.run(segments=segments, video_id=7)

    assert result.video_id == 7
    assert len(result.chapters) >= 1
    for chapter in result.chapters:
        assert chapter.start is not None
        assert chapter.end is not None
        assert chapter.end > chapter.start
        assert chapter.title != ""
