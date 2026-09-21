import logging

from ai.chapter_detection.chapter_detector import ChapterDetector
from ai.chapter_detection.chapter_postprocess import ChapterPostProcessor
from ai.chapter_detection.chapter_result import ChapterResult
from ai.chapter_detection.timestamp_alignment import (
    align_chapters,
    align_topics,
)
from ai.chapter_detection.topic_segmentation import TopicSegmenter
from ai.speech.speech_result import SpeechSegment
from app.config.settings import settings


logger = logging.getLogger(__name__)


class ChapterTopicPipeline:
    """
    Chapter/topic intelligence pipeline:

    segments -> TopicSegmenter -> timestamp alignment (topics) ->
    ChapterDetector -> timestamp alignment (chapters) ->
    ChapterPostProcessor -> ChapterResult.

    Takes already-produced speech segments (Phase 8's SpeechSegment)
    as input - never retranscribes audio or recomputes embeddings
    beyond what topic/chapter detection itself needs. Not coupled to
    FastAPI/HTTP in any way; a caller (e.g. a future processing-
    pipeline stage or API layer) is responsible for producing the
    input segments and persisting/serializing the output.

    A single Embedder (and ChapterLabeler) is constructed here and
    shared between TopicSegmenter and ChapterDetector, instead of
    each defaulting to building its own - both would otherwise load
    the (heavy) embedding model independently for one pipeline run.
    """

    def __init__(
        self,
        topic_segmenter: TopicSegmenter | None = None,
        chapter_detector: ChapterDetector | None = None,
        post_processor: ChapterPostProcessor | None = None,
    ):
        shared_embedder = None

        if (
            topic_segmenter is None or chapter_detector is None
        ) and settings.chapter.use_embedding_segmentation:
            from ai.embedding.embedder import Embedder

            shared_embedder = Embedder()

        self.topic_segmenter = (
            topic_segmenter
            or TopicSegmenter(embedder=shared_embedder)
        )
        self.chapter_detector = (
            chapter_detector
            or ChapterDetector(embedder=shared_embedder)
        )
        self.post_processor = (
            post_processor
            or ChapterPostProcessor()
        )

    def run(
        self,
        segments: list[SpeechSegment],
        video_id: int | None = None,
    ) -> ChapterResult:
        if not segments:
            logger.info(
                "No segments provided; returning an empty ChapterResult.",
            )
            return ChapterResult(
                video_id=video_id,
                chapters=(),
            )

        topics = self.topic_segmenter.segment(segments)
        topics = align_topics(topics, segments)

        chapters = self.chapter_detector.detect(topics, segments)
        chapters = align_chapters(chapters, segments)

        final_chapters = self.post_processor.process(chapters)

        logger.info(
            "Chapter/topic pipeline produced %s chapter(s) for video %s.",
            len(final_chapters),
            video_id,
        )

        return ChapterResult(
            video_id=video_id,
            chapters=tuple(final_chapters),
        )
