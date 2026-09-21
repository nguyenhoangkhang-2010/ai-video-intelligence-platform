import dataclasses
import logging

from ai.chapter_detection.chapter_result import Chapter, Topic
from ai.speech.speech_result import SpeechSegment


logger = logging.getLogger(__name__)


def resolve_boundary(
    segment_indices: tuple[int, ...],
    segments: list[SpeechSegment],
) -> tuple[float | None, float | None, str | None]:
    """
    The single place start/end timestamps (and dominant speaker) are
    ever computed for a topic/chapter - resolved strictly from its
    constituent segment indices against the original segment list,
    so topic/chapter detection logic never invents its own
    timestamps.

    Returns (None, None, None) if segment_indices is empty or every
    index is out of range against `segments` - missing/invalid
    timestamps are handled safely rather than raising, since a
    stray/invalid index should not crash the whole pipeline.
    """

    valid_segments = [
        segments[index]
        for index in segment_indices
        if 0 <= index < len(segments)
    ]

    if not valid_segments:
        return None, None, None

    start = min(segment.start for segment in valid_segments)
    end = max(segment.end for segment in valid_segments)

    speaker_counts: dict[str, int] = {}

    for segment in valid_segments:
        if segment.speaker:
            speaker_counts[segment.speaker] = (
                speaker_counts.get(segment.speaker, 0) + 1
            )

    dominant_speaker = (
        max(speaker_counts, key=speaker_counts.get)
        if speaker_counts
        else None
    )

    return start, end, dominant_speaker


def align_topics(
    topics: list[Topic],
    segments: list[SpeechSegment],
) -> list[Topic]:
    aligned = []

    for topic in topics:
        start, end, speaker = resolve_boundary(
            topic.segment_indices,
            segments,
        )

        if start is None:
            logger.warning(
                "Topic %s has no valid source segments; leaving "
                "timestamps unresolved.",
                topic.id,
            )

        aligned.append(
            dataclasses.replace(
                topic,
                start=start,
                end=end,
                metadata={
                    **topic.metadata,
                    "dominant_speaker": speaker,
                },
            )
        )

    return aligned


def align_chapters(
    chapters: list[Chapter],
    segments: list[SpeechSegment],
) -> list[Chapter]:
    aligned = []

    for chapter in chapters:
        start, end, speaker = resolve_boundary(
            chapter.segment_indices,
            segments,
        )

        if start is None:
            logger.warning(
                "Chapter %s has no valid source segments; leaving "
                "timestamps unresolved.",
                chapter.id,
            )

        aligned.append(
            dataclasses.replace(
                chapter,
                start=start,
                end=end,
                metadata={
                    **chapter.metadata,
                    "dominant_speaker": speaker,
                },
            )
        )

    return aligned
