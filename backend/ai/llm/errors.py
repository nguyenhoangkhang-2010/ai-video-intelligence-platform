"""
Structured error types for LLM provider calls.

Lets callers (RAGPipeline.ask()) distinguish "the LLM genuinely
failed" from a bug, and react to each failure mode deliberately
instead of letting a raw requests/ValueError exception become an
unhandled 500. Every subtype below corresponds to a failure mode this
project has actually hit against its own local Ollama deployment, not
a speculative taxonomy.
"""


class LLMError(Exception):
    """Base type for every LLM-call failure. Safe to catch broadly."""


class LLMConnectionError(LLMError):
    """The LLM endpoint could not be reached (refused/unreachable), even after retrying."""


class LLMTimeoutError(LLMError):
    """
    The LLM endpoint accepted the request but did not respond in
    time. Deliberately distinct from LLMConnectionError: the request
    was genuinely slow, not broken, so callers must not retry this
    the same way they would a connection failure (see
    ollama_client.py's retry policy for why).
    """


class LLMUnavailableError(LLMError):
    """The LLM endpoint returned a non-2xx HTTP status (e.g. model not found, server error)."""


class LLMEmptyResponseError(LLMError):
    """The LLM endpoint returned a well-formed response with no usable text."""


class LLMMalformedResponseError(LLMError):
    """The LLM endpoint's response body could not be parsed as the expected JSON shape."""
