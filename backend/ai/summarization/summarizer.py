import logging

from ai.llm.factory import get_llm_provider
from ai.llm.provider import LLMProvider
from app.config.settings import settings


logger = logging.getLogger(__name__)


class Summarizer:
    """Generate summaries from transcripts."""

    def __init__(
        self,
        llm_client: LLMProvider | None = None,
    ):
        self.llm_client = (
            llm_client
            or get_llm_provider()
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

        max_chars = settings.summary.max_context_chars
        source_text = text[:max_chars]

        prompt = f"""
            Hãy tóm tắt transcript sau bằng tiếng Việt.

            Yêu cầu:
            - Giữ lại các ý chính.
            - Không thêm thông tin không có trong transcript.
            - Viết ngắn gọn, rõ ràng.
            - Chỉ trả về nội dung bản tóm tắt.

            Transcript:
            {source_text}
            """.strip()

        summary = self.llm_client.generate(
            prompt,
        )

        logger.info(
            "Summary generated."
        )

        return summary