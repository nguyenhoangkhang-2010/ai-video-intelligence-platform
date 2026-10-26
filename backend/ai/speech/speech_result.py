from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SpeechSegment:
    """
    A single aligned segment of a video's transcribed audio.

    Unified representation meant to be consumed by any downstream
    stage (summary, embedding, translation, quiz, and future chapter
    detection / knowledge graph work) without each one needing to
    know about ASR/diarization/VAD internals.

    `speaker` is None whenever diarization was not run/enabled or no
    speaker could be confidently attributed to this segment - never a
    fabricated value.
    """

    start: float
    end: float
    text: str
    speaker: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SpeechResult:
    """
    Full output of the speech intelligence pipeline for one video.
    """

    language: str
    text: str
    segments: list[SpeechSegment]
    language_probability: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
