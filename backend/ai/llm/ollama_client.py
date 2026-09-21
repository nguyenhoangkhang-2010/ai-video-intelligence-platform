import logging

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.settings import settings


logger = logging.getLogger(__name__)

# Bounded retry for genuinely transient network failures only (Ollama
# unreachable/slow to accept a connection) - NOT for a well-formed
# response the server chose to send back empty, which is an
# application-level condition retrying the exact same request is
# unlikely to fix differently, and NOT for HTTP error status codes
# (response.raise_for_status()), which usually indicate a request/
# model problem rather than a transient blip.
_retry_ollama_call = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(
        (requests.exceptions.ConnectionError, requests.exceptions.Timeout),
    ),
)


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

    @_retry_ollama_call
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