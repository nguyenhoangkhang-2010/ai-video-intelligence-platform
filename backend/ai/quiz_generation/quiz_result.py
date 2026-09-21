"""Domain representations for generated quiz content."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class QuizQuestion:
    """A single normalized quiz question, independent of question type."""

    question: str
    question_type: str
    correct_answer: str
    options: tuple[str, ...] | None = None
    explanation: str | None = None
    source_segment_ids: tuple[int, ...] = field(default_factory=tuple)
    difficulty: str | None = None
    confidence: float | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class QuizResult:
    """The full set of generated questions for a piece of source content."""

    questions: tuple[QuizQuestion, ...]
    metadata: dict = field(default_factory=dict)
