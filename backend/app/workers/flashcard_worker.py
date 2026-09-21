import logging

from ai.flashcards.flashcard_generator import FlashcardGenerator
from ai.flashcards.flashcard_result import Flashcard
from app.config.settings import settings


logger = logging.getLogger(__name__)


class FlashcardWorker:
    """
    Worker for generating flashcards from transcript text.

    Wraps ai.flashcards.flashcard_generator.FlashcardGenerator and
    adapts its normalized Flashcard output into the plain-dict shape
    consumed by VideoPipelineService.flashcard_stage(), mirroring
    QuizWorker's adapter role.
    """

    def __init__(
        self,
        flashcard_generator: FlashcardGenerator | None = None,
    ):
        self.flashcard_generator = flashcard_generator

    def process(
        self,
        transcript: str,
    ) -> list[dict]:

        logger.info(
            "Generating flashcards.",
        )

        if not settings.flashcard.enabled:
            logger.info(
                "Flashcard LLM generation disabled; returning no "
                "flashcards.",
            )
            return []

        if not transcript or not transcript.strip():
            logger.info(
                "Empty transcript; no flashcards generated.",
            )
            return []

        generator = self.flashcard_generator or FlashcardGenerator()

        try:
            result = generator.generate(text=transcript)
        except Exception:
            logger.warning(
                "Flashcard generation failed; returning no flashcards.",
                exc_info=True,
            )
            return []

        flashcards = [
            _to_dict(card)
            for card in result.cards
        ]

        logger.info(
            "Flashcards generated.",
        )

        return flashcards


def _to_dict(
    card: Flashcard,
) -> dict:
    return {
        "question": card.front,
        "answer": card.back,
        "difficulty": card.difficulty or "medium",
    }
