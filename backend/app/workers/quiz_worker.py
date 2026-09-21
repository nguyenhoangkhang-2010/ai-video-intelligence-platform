import logging

from ai.quiz_generation.quiz_generator import QuizGenerator
from ai.quiz_generation.quiz_result import QuizQuestion
from app.config.settings import settings


logger = logging.getLogger(__name__)


class QuizWorker:
    """
    Worker for generating quizzes from transcript text.

    Wraps ai.quiz_generation.quiz_generator.QuizGenerator (MCQ +
    True/False + Short-Answer) and adapts its normalized QuizQuestion
    output into the plain-dict shape VideoPipelineService.quiz_stage()
    already consumes, so the pipeline call site needs no changes.
    """

    def __init__(
        self,
        quiz_generator: QuizGenerator | None = None,
    ):
        self.quiz_generator = quiz_generator

    def process(
        self,
        transcript: str,
    ) -> list[dict]:

        logger.info(
            "Generating quiz.",
        )

        if not settings.quiz.enabled:
            logger.info(
                "Quiz LLM generation disabled; returning no quizzes.",
            )
            return []

        if not transcript or not transcript.strip():
            logger.info(
                "Empty transcript; no quizzes generated.",
            )
            return []

        generator = self.quiz_generator or QuizGenerator()

        try:
            result = generator.generate(text=transcript)
        except Exception:
            logger.warning(
                "Quiz generation failed; returning no quizzes.",
                exc_info=True,
            )
            return []

        quizzes = [
            _to_dict(question)
            for question in result.questions
        ]

        logger.info(
            "Quiz generated.",
        )

        return quizzes


def _to_dict(
    question: QuizQuestion,
) -> dict:
    return {
        "type": question.question_type,
        "question": question.question,
        "answer": question.correct_answer,
        "options": (
            ",".join(question.options)
            if question.options
            else None
        ),
    }
