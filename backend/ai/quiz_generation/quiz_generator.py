"""Orchestrates MCQ, True/False, and Short-Answer quiz generation."""
import logging

from ai.llm.ollama_client import OllamaClient
from ai.quiz_generation.mcq import MCQGenerator
from ai.quiz_generation.quiz_result import QuizQuestion, QuizResult
from ai.quiz_generation.short_answer import ShortAnswerGenerator
from ai.quiz_generation.true_false import TrueFalseGenerator
from app.config.settings import settings

logger = logging.getLogger(__name__)


class QuizGenerator:
    """
    Generates a mixed-type quiz from source text (transcript, optionally
    scoped to a chapter/topic). Composes the per-type generators and
    applies configured question counts from settings.
    """

    def __init__(
        self,
        llm_client: OllamaClient | None = None,
        mcq_generator: MCQGenerator | None = None,
        true_false_generator: TrueFalseGenerator | None = None,
        short_answer_generator: ShortAnswerGenerator | None = None,
    ):
        shared_client = llm_client or OllamaClient()

        self.mcq_generator = mcq_generator or MCQGenerator(
            llm_client=shared_client,
        )
        self.true_false_generator = (
            true_false_generator
            or TrueFalseGenerator(llm_client=shared_client)
        )
        self.short_answer_generator = (
            short_answer_generator
            or ShortAnswerGenerator(llm_client=shared_client)
        )

    def generate(
        self,
        text: str,
        mcq_count: int | None = None,
        true_false_count: int | None = None,
        short_answer_count: int | None = None,
    ) -> QuizResult:
        if mcq_count is None:
            mcq_count = settings.quiz.mcq_count
        if true_false_count is None:
            true_false_count = settings.quiz.true_false_count
        if short_answer_count is None:
            short_answer_count = settings.quiz.short_answer_count

        if not text or not text.strip():
            return QuizResult(questions=())

        max_chars = settings.quiz.max_context_chars
        source_text = text[:max_chars]

        questions: list[QuizQuestion] = []

        if mcq_count > 0:
            questions.extend(
                self.mcq_generator.generate(
                    text=source_text, count=mcq_count,
                ),
            )

        if true_false_count > 0:
            questions.extend(
                self.true_false_generator.generate(
                    text=source_text, count=true_false_count,
                ),
            )

        if short_answer_count > 0:
            questions.extend(
                self.short_answer_generator.generate(
                    text=source_text, count=short_answer_count,
                ),
            )

        return QuizResult(
            questions=tuple(questions),
            metadata={"source_length": len(text)},
        )
