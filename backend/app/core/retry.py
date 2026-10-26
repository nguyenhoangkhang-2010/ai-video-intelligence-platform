"""
Shared retry classification: which exceptions represent a transient
infrastructure failure (worth a bounded retry) versus a permanent/
application error (retrying would not help, so failing fast and
clearly is the correct behavior).

Used by:
- ai.llm.ollama_client.OllamaClient.generate() (tenacity retry around
  a single HTTP call to Ollama) - note OllamaClient's own retry
  predicate is the narrower, explicit
  retry_if_exception_type(requests.exceptions.ConnectionError), not
  this tuple, so adding LLMConnectionError/etc. below does not change
  OllamaClient's own internal retry behavior at all.
- app.workers.celery_app (Celery task-level `autoretry_for` on
  process_video - see that module's docstring for why this only
  matters for failures that happen *before* a ProcessingJob is
  claimed; failures inside the pipeline are correctly NOT retried at
  the task level today).
- Phase B's per-stage orchestration loop (VideoPipelineService.
  process()), which uses is_transient_error() to decide, when a
  stage fails, whether the exception it collected is worth leaving
  retryable (re-raised so Celery's autoretry_for sees it and the
  stage is picked up again on redelivery) versus a deterministic
  failure not worth retrying.

Deliberately narrow: only exceptions that unambiguously mean "could
not reach/complete a call to an external service right now" are
listed. Business/data errors (e.g. "no speech detected in audio", a
malformed LLM JSON response already handled by ai.llm.json_utils,
a 4xx from a well-formed-but-rejected request) are NOT included -
retrying those would just fail again identically.

LLMConnectionError/LLMTimeoutError/LLMUnavailableError (see
ai.llm.errors) are included for the same reason requests.
exceptions.ConnectionError/Timeout already were - they mean exactly
"could not reach/complete this call to Ollama right now". Found while
implementing Phase B: these were raised by every video-processing
stage that calls an LLM (summary/translation/quiz/flashcard - chapter
labeling already catches its own LLM failures internally) but were
NOT in this tuple, so they propagated to the Celery task boundary
without ever being recognized as retryable - a real, narrower version
of the same class of gap Phase 1 fixed for the RAG chat path.
LLMEmptyResponseError/LLMMalformedResponseError are deliberately NOT
included, matching Phase 1's own documented reasoning: an empty or
malformed response is an application-level condition a retry is not
expected to fix.
"""
import redis.exceptions
import requests.exceptions
from sqlalchemy.exc import DBAPIError, OperationalError

from ai.llm.errors import (
    LLMConnectionError,
    LLMTimeoutError,
    LLMUnavailableError,
)

TRANSIENT_EXCEPTIONS: tuple[type[Exception], ...] = (
    # Database: connection could not be established/was dropped.
    OperationalError,
    DBAPIError,
    # Redis (Celery broker/result backend).
    redis.exceptions.ConnectionError,
    redis.exceptions.TimeoutError,
    # HTTP calls to external services (Ollama, etc.).
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    # Generic network-layer failures.
    ConnectionError,
    TimeoutError,
    # LLM provider call failures (see ai.llm.errors) - connection/
    # timeout/unavailable are transient; empty/malformed response are
    # deliberately excluded (see module docstring above).
    LLMConnectionError,
    LLMTimeoutError,
    LLMUnavailableError,
)


def is_transient_error(exc: BaseException) -> bool:
    """True if `exc` represents a likely-transient infrastructure failure worth retrying."""
    return isinstance(exc, TRANSIENT_EXCEPTIONS)
