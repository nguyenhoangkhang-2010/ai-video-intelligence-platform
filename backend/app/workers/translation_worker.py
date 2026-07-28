import logging

from ai.translation.translator import Translator


logger = logging.getLogger(__name__)


class TranslationWorker:
    """Worker for transcript translation."""

    def __init__(
        self,
    ):
        self.translator = Translator()

    def process(
        self,
        transcript: str,
        target_language: str,
    ) -> dict:
        """
        Generate translation from transcript.
        """
        logger.info(
            "Start translation worker.",
        )

        subtitle = self.translator.translate(
            transcript,
            target_language,
        )

        logger.info(
            "Translation completed.",
        )

        return {
            "language": target_language,
            "subtitle": subtitle,
        }