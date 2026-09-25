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
# unreachable/refusing the connection) - NOT for a well-formed
# response the server chose to send back empty, which is an
# application-level condition retrying the exact same request is
# unlikely to fix differently, and NOT for HTTP error status codes
# (response.raise_for_status()), which usually indicate a request/
# model problem rather than a transient blip.
#
# Deliberately NOT retried: requests.exceptions.Timeout. A read
# timeout means Ollama accepted the request and was still generating
# when the timeout fired - the request was genuinely slow, not
# broken, so retrying the identical prompt is expected to be just as
# slow again. Retrying it anyway turns one already-slow generation
# (up to `timeout` seconds) into a worst case of stop_after_attempt
# separate full-length waits stacked back to back - confirmed live
# against this project's own CPU-only Ollama deployment, where a
# single slow-but-successful generation compounded into a multi-
# minute hang this way. ConnectionError (Ollama not accepting
# connections at all) is unaffected and still retried.
_retry_ollama_call = retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(
        requests.exceptions.ConnectionError,
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