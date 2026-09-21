"""Domain representations for generated flashcard content."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Flashcard:
    """A single study flashcard grounded in source content."""

    front: str
    back: str
    source_segment_ids: tuple[int, ...] = field(default_factory=tuple)
    chapter_id: int | None = None
    topic_index: int | None = None
    difficulty: str | None = None
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class FlashcardResult:
    """The full set of generated flashcards for a piece of source content."""

    cards: tuple[Flashcard, ...]
    metadata: dict = field(default_factory=dict)
