from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Topic:
    """
    A semantically coherent span of segments within a video.

    `start`/`end` are intentionally None until the timestamp
    alignment stage resolves them from `segment_indices` against the
    original segment list - topic/chapter detection logic never
    invents its own timestamps (see ai.chapter_detection.
    timestamp_alignment).

    `segment_indices` are positions into the source segment list
    (e.g. Phase 8's SpeechSegment list) this topic was derived from -
    never dropped, so downstream stages can always trace a topic back
    to its original content.
    """

    id: str
    label: str
    segment_indices: tuple[int, ...]
    start: float | None = None
    end: float | None = None
    score: float | None = None
    keywords: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Chapter:
    """
    A higher-level grouping of one or more Topics.
    """

    id: str
    title: str
    topics: tuple[Topic, ...]
    segment_indices: tuple[int, ...]
    start: float | None = None
    end: float | None = None
    summary: str | None = None
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ChapterResult:
    """
    Full output of the chapter/topic intelligence pipeline for one
    video.
    """

    video_id: int | None
    chapters: tuple[Chapter, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
