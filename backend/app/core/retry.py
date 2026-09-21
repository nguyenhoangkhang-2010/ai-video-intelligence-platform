"""
Shared retry classification: which exceptions represent a transient
infrastructure failure (worth a bounded retry) versus a permanent/
application error (retrying would not help, so failing fast and
clearly is the correct behavior).

Used by:
- ai.llm.ollama_client.OllamaClient.generate() (tenacity retry around
  a single HTTP call to Ollama).
- app.workers.celery_app (Celery task-level `autoretry_for` on
  process_video - see that module's docstring for why this only
  matters for failures that happen *before* a ProcessingJob is
  claimed; failures inside the pipeline are correctly NOT retried at
  the task level).

Deliberately narrow: only exceptions that unambiguously mean "could
not reach/complete a call to an external service right now" are
listed. Business/data errors (e.g. "no speech detected in audio", a
malformed LLM JSON response already handled by ai.llm.json_utils,
a 4xx from a well-formed-but-rejected request) are NOT included -
retrying those would just fail again identically.
"""
import redis.exceptions
import requests.exceptions
from sqlalchemy.exc import DBAPIError, OperationalError

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
)


def is_transient_error(exc: BaseException) -> bool:
    """True if `exc` represents a likely-transient infrastructure failure worth retrying."""
    return isinstance(exc, TRANSIENT_EXCEPTIONS)
