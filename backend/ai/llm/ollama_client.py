import json
import logging
from collections.abc import Iterator

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config.settings import settings

from ai.llm.errors import (
    LLMConnectionError,
    LLMEmptyResponseError,
    LLMMalformedResponseError,
    LLMTimeoutError,
    LLMUnavailableError,
)


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
    def _post(
        self,
        prompt: str,
    ) -> requests.Response:
        """
        Raw, retried network call only - kept separate from `generate`
        so the bounded-retry decorator (ConnectionError only, see
        module docstring) never sees the translated LLMError types
        below and so a caller catching those never has to also catch
        a raw `requests`/`ValueError` leaking from this layer.
        """
        return requests.post(
            f"{self.base_url}/api/generate",
            json=self._request_body(prompt, stream=False),
            timeout=settings.llm.request_timeout_seconds,
        )

    def _request_body(
        self,
        prompt: str,
        stream: bool,
    ) -> dict:
        body = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        # settings.llm.think: False/True is sent as-is; None omits the
        # option for models or Ollama versions that don't accept it.
        if settings.llm.think is not None:
            body["think"] = settings.llm.think
        return body

    def generate(
        self,
        prompt: str,
    ) -> str:
        """
        Generate text using Ollama.

        Raises one of ai.llm.errors.LLMError's subtypes for every
        failure mode this has actually hit in practice - never a raw
        requests/ValueError - so a caller (RAGPipeline.ask()) can
        catch one base type and degrade gracefully instead of letting
        an LLM hiccup become an unhandled 500.
        """
        try:
            response = self._post(prompt)
        except requests.exceptions.ConnectionError as exc:
            # tenacity already retried this up to 3 times (reraise=True
            # re-raises the final attempt's exception unchanged) -
            # reaching here means every attempt failed.
            raise LLMConnectionError(
                f"Could not reach Ollama at {self.base_url} after retrying."
            ) from exc
        except requests.exceptions.Timeout as exc:
            # Deliberately not retried - see module docstring.
            raise LLMTimeoutError(
                f"Ollama did not respond within "
                f"{settings.llm.request_timeout_seconds}s."
            ) from exc

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise LLMUnavailableError(
                f"Ollama returned HTTP {response.status_code}."
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise LLMMalformedResponseError(
                "Ollama response body was not valid JSON."
            ) from exc

        result = data.get("response", "").strip()

        if not result:
            raise LLMEmptyResponseError(
                "Ollama returned an empty response."
            )

        return result

    @_retry_ollama_call
    def _post_stream(
        self,
        prompt: str,
    ) -> requests.Response:
        """
        Streaming counterpart of `_post`: same bounded retry on
        ConnectionError, but `stream=True` on both the Ollama request
        and the HTTP response. The (connect, read) timeout makes the
        read timeout apply *between* chunks, so a long answer that
        keeps producing tokens never times out - only a stalled one.
        """
        return requests.post(
            f"{self.base_url}/api/generate",
            json=self._request_body(prompt, stream=True),
            timeout=(10, settings.llm.request_timeout_seconds),
            stream=True,
        )

    def generate_stream(
        self,
        prompt: str,
    ) -> Iterator[str]:
        """
        Generate text using Ollama, yielding the answer piece by piece
        as the model produces it (Ollama's newline-delimited JSON
        stream). Only the visible `response` text is yielded; a
        reasoning model's separate `thinking` field is ignored, the
        same as `generate` does.

        Raises the same ai.llm.errors.LLMError subtypes as `generate`
        - before the first piece (connection, timeout, HTTP status)
        or in the middle of the stream (a stalled or dropped
        connection, a malformed line, an error object from Ollama).
        """
        try:
            response = self._post_stream(prompt)
        except requests.exceptions.ConnectionError as exc:
            raise LLMConnectionError(
                f"Could not reach Ollama at {self.base_url} after retrying."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise LLMTimeoutError(
                f"Ollama did not respond within "
                f"{settings.llm.request_timeout_seconds}s."
            ) from exc

        with response:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                raise LLMUnavailableError(
                    f"Ollama returned HTTP {response.status_code}."
                ) from exc

            produced_any = False

            try:
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except ValueError as exc:
                        raise LLMMalformedResponseError(
                            "Ollama stream contained a line that was not valid JSON."
                        ) from exc

                    if data.get("error"):
                        raise LLMUnavailableError(
                            f"Ollama reported an error: {data['error']}"
                        )

                    piece = data.get("response", "")
                    if piece:
                        produced_any = True
                        yield piece

                    if data.get("done"):
                        break
            except requests.exceptions.Timeout as exc:
                raise LLMTimeoutError(
                    "Ollama stopped sending output for longer than "
                    f"{settings.llm.request_timeout_seconds}s."
                ) from exc
            except requests.exceptions.RequestException as exc:
                # A dropped connection mid-stream (including a read
                # timeout surfaced by urllib3 as a connection error).
                raise LLMConnectionError(
                    "The connection to Ollama was interrupted mid-answer."
                ) from exc

            if not produced_any:
                raise LLMEmptyResponseError(
                    "Ollama returned an empty response."
                )