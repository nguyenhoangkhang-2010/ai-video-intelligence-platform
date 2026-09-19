import logging

from ai.llm.ollama_client import OllamaClient


logger = logging.getLogger(__name__)


class Summarizer:
    """Generate summaries from transcripts."""

    def __init__(
        self,
        llm_client: OllamaClient | None = None,
    ):
        self.llm_client = (
            llm_client
            or OllamaClient()
        )

    def summarize(
        self,
        text: str,
    ) -> str:
        """
        Generate a summary from transcript text.
        """

        if not text or not text.strip():
            raise ValueError(
                "Transcript text cannot be empty."
            )

        logger.info(
            "Generating summary."
        )

        prompt = f"""
            Hãy tóm tắt transcript sau bằng tiếng Việt.

            Yêu cầu:
            - Giữ lại các ý chính.
            - Không thêm thông tin không có trong transcript.
            - Viết ngắn gọn, rõ ràng.
            - Chỉ trả về nội dung bản tóm tắt.

            Transcript:
            {text}
            """.strip()

        summary = self.llm_client.generate(
            prompt,
        )

        logger.info(
            "Summary generated."
        )

        return summary