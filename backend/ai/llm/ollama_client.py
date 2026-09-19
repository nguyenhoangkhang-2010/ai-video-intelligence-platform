import logging

import requests

from app.config.settings import settings


logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.base_url = (
            base_url
            or settings.llm.ollama_base_url
        )
        self.model = (
            model
            or settings.llm.default_llm
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        """Generate text using Ollama."""

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300,
        )

        response.raise_for_status()

        data = response.json()

        result = data.get("response", "").strip()

        if not result:
            raise ValueError(
                "Ollama returned an empty response."
            )

        return result