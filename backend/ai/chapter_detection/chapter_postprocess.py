import dataclasses
import logging

from ai.chapter_detection.chapter_result import Chapter
from app.config.settings import settings


logger = logging.getLogger(__name__)


class ChapterPostProcessor:
    """
    Normalizes a list of (already timestamp-aligned) chapters into a
    stable, final list:

    - drops chapters with missing/invalid timestamps or no source
      segments (never fabricates a replacement)
    - orders chronologically
    - normalizes titles (whitespace only - never rewrites content)
    - merges a chapter shorter than `min_chapter_duration_seconds`,
      or one with the exact same title as its predecessor, into the
      previous chapter (source segment references are combined, never
      dropped)
    - clamps scores into [0, 1] if present

    Deterministic given the same input and configuration.
    """

    def __init__(
        self,
        min_chapter_duration_seconds: float | None = None,
    ):
        self.min_chapter_duration_seconds = (
            min_chapter_duration_seconds
            if min_chapter_duration_seconds is not None
            else settings.chapter.min_chapter_duration_seconds
        )

    def process(
        self,
        chapters: list[Chapter],
    ) -> list[Chapter]:
        if not chapters:
            return []

        valid = [
            chapter
            for chapter in chapters
            if (
                chapter.start is not None
                and chapter.end is not None
                and chapter.end > chapter.start
                and chapter.segment_indices
            )
        ]

        valid.sort(key=lambda chapter: chapter.start)

        normalized = [
            dataclasses.replace(
                chapter,
                title=self._normalize_title(chapter.title),
                score=self._clamp_score(chapter.score),
            )
            for chapter in valid
        ]

        merged: list[Chapter] = []

        for chapter in normalized:
            if merged and self._should_merge(merged[-1], chapter):
                merged[-1] = self._merge(merged[-1], chapter)
            else:
                merged.append(chapter)

        logger.info(
            "Chapter post-processing: %s input -> %s final chapter(s).",
            len(chapters),
            len(merged),
        )

        return merged

    def _should_merge(
        self,
        previous: Chapter,
        current: Chapter,
    ) -> bool:
        duration = previous.end - previous.start

        same_title = (
            bool(previous.title)
            and previous.title == current.title
        )

        return (
            duration < self.min_chapter_duration_seconds
            or same_title
        )

    @staticmethod
    def _merge(
        previous: Chapter,
        current: Chapter,
    ) -> Chapter:
        return dataclasses.replace(
            previous,
            end=max(previous.end, current.end),
            segment_indices=tuple(
                sorted(
                    set(previous.segment_indices)
                    | set(current.segment_indices)
                )
            ),
            topics=previous.topics + current.topics,
            title=previous.title or current.title,
        )

    @staticmethod
    def _normalize_title(
        title: str,
    ) -> str:
        if not title:
            return ""

        return " ".join(title.strip().split())

    @staticmethod
    def _clamp_score(
        score: float | None,
    ) -> float | None:
        if score is None:
            return None

        return max(0.0, min(1.0, score))
