import logging

logger = logging.getLogger(__name__)


class Translator:
    """Translation generator."""

    def translate(
        self,
        text: str,
        target_language: str,
    ) -> str:
        """
        Translate transcript into target language.
        """
        logger.info(
            "Generating translation.",
        )

        return text