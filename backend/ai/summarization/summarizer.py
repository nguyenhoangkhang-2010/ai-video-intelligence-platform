import logging

logger = logging.getLogger(__name__)


class Summarizer:
    """Generate summaries from transcripts."""
    def summarize(
        self,
        text: str,
    ) -> str:
        """
        Generate a summary from transcript text.
        """
        logger.info(
            "Generating summary.",
        )
        # TODO:
        # Replace with LLM summarization.
        summary = text.strip()
        logger.info(
            "Summary generated.",
        )
        return summary