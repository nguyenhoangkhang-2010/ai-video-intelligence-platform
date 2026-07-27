import logging

from ai.summarization.summarizer import Summarizer


logger = logging.getLogger(__name__)


class SummaryWorker:
    """Worker for transcript summarization."""
    def __init__(
        self,
    ):
        self.summarizer = Summarizer()

    def process(
        self,
        transcript: str,
    ) -> dict:
        """
        Generate summary from transcript.
        """
        logger.info(
            "Start summary worker.",
        )
        summary = self.summarizer.summarize(
            transcript,
        )
        logger.info(
            "Summary completed.",
        )
        return {
            "type": "default",
            "content": summary,
            "model_name": "stub",
        }