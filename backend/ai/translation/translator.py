import logging

from ai.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class Translator:
    """
    Translation generator, backed by the same Ollama LLM already used
    for summaries/quizzes/flashcards/chapters (see
    ai/llm/ollama_client.py) - no new model/dependency/external
    service is introduced.
    """

    def __init__(
        self,
        llm_client: OllamaClient | None = None,
    ):
        self.llm_client = (
            llm_client
            or OllamaClient()
        )

    def translate(
        self,
        text: str,
        target_language: str,
        source_language: str | None = None,
    ) -> str:
        """
        Translate transcript text into `target_language` (an ISO
        639-1 code, e.g. "en").

        If `source_language` is already the same as `target_language`
        (case-insensitive), the text is already in the target
        language, so it is returned unchanged instead of being sent
        through the LLM - the one case where "output equals input" is
        actually correct rather than the previous no-op bug (which
        returned the input unchanged regardless of source language
        and persisted it mislabeled as a translation).
        """
        if not text or not text.strip():
            raise ValueError(
                "Transcript text cannot be empty."
            )

        if (
            source_language
            and source_language.strip().lower() == target_language.strip().lower()
        ):
            logger.info(
                "Source language (%s) already matches target language "
                "(%s); skipping translation.",
                source_language,
                target_language,
            )
            return text

        logger.info(
            "Generating translation into %s.",
            target_language,
        )

        prompt = f"""
            Translate the following transcript into the language with
            ISO 639-1 code "{target_language}".

            Requirements:
            - Preserve the original meaning; do not add, remove, or
              summarize any content.
            - Keep the translation natural and fluent in the target
              language.
            - Return only the translated text, with no commentary,
              labels, or explanation.

            Transcript:
            {text}
            """.strip()

        translation = self.llm_client.generate(
            prompt,
        )

        logger.info(
            "Translation generated.",
        )

        return translation
