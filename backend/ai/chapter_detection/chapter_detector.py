import logging

from ai.chapter_detection.chapter_result import Chapter, Topic
from ai.chapter_detection.similarity import cosine_similarity
from ai.speech.speech_result import SpeechSegment
from app.config.settings import settings


logger = logging.getLogger(__name__)

_UNSET = object()


class ChapterDetector:
    """
    Groups topics into higher-level chapters.

    Adjacent topics are merged into the same chapter while their
    representative embeddings stay similar enough (topic continuity),
    capped at a configurable maximum topic count per chapter - never
    a fixed/arbitrary rule about specific topic content (no
    "if topic == X then chapter Y"). Reuses the same embedding
    infrastructure as TopicSegmentation; falls back to simple
    fixed-size grouping when no embedder is available.

    Chapter titles are generated via the existing LLM infrastructure
    (ai.llm.chapter_labeler.ChapterLabeler, itself a thin wrapper
    around the existing OllamaClient - no new/unrelated LLM client),
    with a deterministic non-LLM fallback baked into the labeler
    itself.
    """

    def __init__(
        self,
        embedder=_UNSET,
        labeler=_UNSET,
        max_topics_per_chapter: int | None = None,
        similarity_threshold: float | None = None,
    ):
        self.max_topics_per_chapter = max(
            1,
            (
                max_topics_per_chapter
                if max_topics_per_chapter is not None
                else settings.chapter.max_topics_per_chapter
            ),
        )
        self.similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else settings.chapter.chapter_similarity_threshold
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

        if labeler is not _UNSET:
            self.labeler = labeler
        elif settings.chapter.use_llm_labeling:
            from ai.llm.chapter_labeler import ChapterLabeler

            self.labeler = ChapterLabeler()
        else:
            self.labeler = None

    def detect(
        self,
        topics: list[Topic],
        segments: list[SpeechSegment],
    ) -> list[Chapter]:
        if not topics:
            return []

        groups = self._group_topics(topics, segments)

        chapters = []

        for position, group in enumerate(groups):
            segment_indices = tuple(
                sorted(
                    {
                        index
                        for topic in group
                        for index in topic.segment_indices
                    }
                )
            )

            title = self._label(group, segments)

            chapters.append(
                Chapter(
                    id=f"chapter-{position}",
                    title=title,
                    topics=tuple(group),
                    segment_indices=segment_indices,
                )
            )

        logger.info(
            "Chapter detection grouped %s topic(s) into %s chapter(s).",
            len(topics),
            len(chapters),
        )

        return chapters

    def _group_topics(
        self,
        topics: list[Topic],
        segments: list[SpeechSegment],
    ) -> list[list[Topic]]:
        if self.embedder is None:
            return self._windowed_groups(topics)

        try:
            representative_vectors = [
                self.embedder.embed_query(
                    self._representative_text(topic, segments),
                )
                for topic in topics
            ]
        except Exception:
            logger.warning(
                "Embedding-based chapter grouping failed; falling "
                "back to fixed-size grouping.",
                exc_info=True,
            )
            return self._windowed_groups(topics)

        if any(not vector for vector in representative_vectors):
            logger.warning(
                "Embedder returned an empty vector; falling back to "
                "fixed-size chapter grouping.",
            )
            return self._windowed_groups(topics)

        groups: list[list[Topic]] = [[topics[0]]]

        for index in range(1, len(topics)):
            similarity = cosine_similarity(
                representative_vectors[index - 1],
                representative_vectors[index],
            )

            current_group = groups[-1]

            if (
                similarity >= self.similarity_threshold
                and len(current_group) < self.max_topics_per_chapter
            ):
                current_group.append(topics[index])
            else:
                groups.append([topics[index]])

        return groups

    def _windowed_groups(
        self,
        topics: list[Topic],
    ) -> list[list[Topic]]:
        return [
            topics[i:i + self.max_topics_per_chapter]
            for i in range(0, len(topics), self.max_topics_per_chapter)
        ]

    def _label(
        self,
        group: list[Topic],
        segments: list[SpeechSegment],
    ) -> str:
        text = " ".join(
            self._representative_text(topic, segments)
            for topic in group
        )

        if self.labeler is not None:
            return self.labeler.label(text)

        words = text.strip().split()
        snippet = " ".join(words[:8])
        return snippet or "Untitled Chapter"

    @staticmethod
    def _representative_text(
        topic: Topic,
        segments: list[SpeechSegment],
    ) -> str:
        return " ".join(
            segments[index].text
            for index in topic.segment_indices
            if 0 <= index < len(segments)
        )
