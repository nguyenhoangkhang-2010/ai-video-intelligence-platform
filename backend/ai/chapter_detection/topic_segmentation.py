import logging

from ai.chapter_detection.chapter_result import Topic
from ai.chapter_detection.similarity import cosine_similarity
from ai.speech.speech_result import SpeechSegment
from app.config.settings import settings


logger = logging.getLogger(__name__)

_UNSET = object()


class TopicSegmenter:
    """
    Splits a video's speech segments into semantically coherent
    topics.

    Reuses the existing embedding infrastructure (ai.embedding.
    embedder.Embedder - the same model/class RAG and semantic search
    use) to detect topic boundaries where consecutive segments'
    similarity drops below a configurable threshold, rather than
    introducing a second embedding model/service. No topic label is
    hardcoded from transcript content - labels here are generic
    placeholders; real titles are produced later by
    ai.llm.chapter_labeler.ChapterLabeler (see ChapterDetector).

    Degrades gracefully to a generic, non-semantic fixed-window
    segmentation when no embedder is available/enabled, or when
    embedding generation fails - chapter/topic detection must never
    hard-fail just because the embedding model couldn't run.
    """

    def __init__(
        self,
        embedder=_UNSET,
        similarity_threshold: float | None = None,
        min_topic_segments: int | None = None,
    ):
        self.similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.chapter.topic_similarity_threshold
        )
        self.min_topic_segments = max(
            1,
            (
                min_topic_segments
                if min_topic_segments is not None
                else settings.chapter.min_topic_segments
            ),
        )

        if embedder is not _UNSET:
            # Explicit value (including None, meaning "no embedder,
            # always use the fallback") always wins over settings.
            self.embedder = embedder
        elif settings.chapter.use_embedding_segmentation:
            from ai.embedding.embedder import Embedder

            self.embedder = Embedder()
        else:
            self.embedder = None

    def segment(
        self,
        segments: list[SpeechSegment],
    ) -> list[Topic]:
        if not segments:
            return []

        boundaries = self._detect_boundaries(segments)

        topics = []

        for position, start_index in enumerate(boundaries):
            end_index = (
                boundaries[position + 1] - 1
                if position + 1 < len(boundaries)
                else len(segments) - 1
            )

            indices = tuple(range(start_index, end_index + 1))

            topics.append(
                Topic(
                    id=f"topic-{position}",
                    label=f"Topic {position + 1}",
                    segment_indices=indices,
                )
            )

        logger.info(
            "Topic segmentation produced %s topic(s) from %s segment(s).",
            len(topics),
            len(segments),
        )

        return topics

    def _detect_boundaries(
        self,
        segments: list[SpeechSegment],
    ) -> list[int]:
        if self.embedder is None or len(segments) <= self.min_topic_segments:
            return self._windowed_boundaries(len(segments))

        try:
            vectors = [
                self.embedder.embed_query(segment.text)
                for segment in segments
            ]
        except Exception:
            logger.warning(
                "Embedding-based topic segmentation failed; "
                "falling back to fixed-window segmentation.",
                exc_info=True,
            )
            return self._windowed_boundaries(len(segments))

        if any(not vector for vector in vectors):
            logger.warning(
                "Embedder returned an empty vector; falling back to "
                "fixed-window segmentation.",
            )
            return self._windowed_boundaries(len(segments))

        boundaries = [0]

        for index in range(1, len(vectors)):
            similarity = cosine_similarity(
                vectors[index - 1],
                vectors[index],
            )

            far_enough_from_last_boundary = (
                index - boundaries[-1] >= self.min_topic_segments
            )

            if (
                similarity < self.similarity_threshold
                and far_enough_from_last_boundary
            ):
                boundaries.append(index)

        return boundaries

    def _windowed_boundaries(
        self,
        segment_count: int,
    ) -> list[int]:
        if segment_count == 0:
            return []

        window = self.min_topic_segments

        return list(range(0, segment_count, window))
