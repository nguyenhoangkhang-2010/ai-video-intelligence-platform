"""
Application/worker logging configuration.

Provides one consistent log format shared by the FastAPI process and
Celery worker processes: timestamp, level, logger name, an HTTP
request_id (set by app.middleware.request_id) or Celery task
name/id (set by the signal handlers in app.workers.celery_app) when
available, and the message. A JSON line format is available for
log-aggregation-friendly environments (LOG_JSON=True); a
human-readable line format is the default for local development.

Only the fields above are ever attached - request/response bodies,
headers, tokens, and other request data are never logged here.
"""
import contextvars
import json
import logging
import sys

from app.config.settings import settings

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None,
)

task_context_var: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "task_context", default=None,
)

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


class ContextFilter(logging.Filter):
    """Attaches the current request_id/Celery task context, if any, to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()

        task_context = task_context_var.get()
        record.task_name = task_context.get("task_name") if task_context else None
        record.task_id = task_context.get("task_id") if task_context else None

        return True


class PlainFormatter(logging.Formatter):
    """Human-readable formatter that appends context fields when present."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)

        context_bits = []
        if getattr(record, "request_id", None):
            context_bits.append(f"request_id={record.request_id}")
        if getattr(record, "task_name", None):
            context_bits.append(f"task={record.task_name}")
        if getattr(record, "task_id", None):
            context_bits.append(f"task_id={record.task_id}")

        if context_bits:
            return f"{base} | {' '.join(context_bits)}"

        return base


class JsonFormatter(logging.Formatter):
    """One-JSON-object-per-line formatter for log-aggregation pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if getattr(record, "request_id", None):
            payload["request_id"] = record.request_id
        if getattr(record, "task_name", None):
            payload["task_name"] = record.task_name
        if getattr(record, "task_id", None):
            payload["task_id"] = record.task_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload)


def _build_formatter() -> logging.Formatter:
    if settings.logging.json_format:
        return JsonFormatter()

    return PlainFormatter(_LOG_FORMAT)


def setup_logging() -> None:
    """
    Configure the root logger for this process (FastAPI app or a
    Celery worker). Idempotent/safe to call more than once - replaces
    any previously installed handlers rather than stacking duplicates.

    Log level is environment-driven (settings.logging.level /
    LOG_LEVEL), defaulting to INFO.
    """
    root = logging.getLogger()
    root.setLevel(settings.logging.level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_build_formatter())
    handler.addFilter(ContextFilter())

    root.handlers = [handler]
