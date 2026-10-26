"""
Celery worker-side Prometheus metrics.

Runs inside the worker process(es) - a separate OS process (and
therefore a separate prometheus_client registry) from the FastAPI API
process, which has its own metrics in app.core.metrics. Exposed on
its own HTTP port (settings.metrics.worker_metrics_port, default
9100) via prometheus_client.start_http_server(), started once when
the worker process boots.

Multiprocess caveat: Celery's default "prefork" pool forks one child
process per configured concurrency slot, and prometheus_client's
in-memory registry is per-process - metrics recorded in a forked child
are invisible to an exporter server started in a different process.
This module assumes/recommends worker concurrency=1 (already a
reasonable choice for this project's heavy AI tasks - see
docs/deployment.md), under which there is exactly one process and the
per-process registry assumption holds. With concurrency > 1, only the
process that first wins the port binds the exporter and metrics from
sibling processes are not counted - documented as a known limitation
rather than solved with prometheus_client's multiprocess mode, which
would add real complexity (a shared PROMETHEUS_MULTIPROC_DIR, a
different metrics-collection code path) for a case this project does
not currently run in.
"""
import logging
import time

from celery.signals import (
    task_failure,
    task_postrun,
    task_prerun,
    task_success,
    worker_process_init,
)
from prometheus_client import Counter, Histogram, start_http_server

from app.config.settings import settings

logger = logging.getLogger(__name__)

CELERY_TASK_TOTAL = Counter(
    "celery_task_total",
    "Total Celery tasks processed, by task name and final status.",
    ["task_name", "status"],
)

CELERY_TASK_DURATION_SECONDS = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds, by task name.",
    ["task_name"],
)

_task_start_times: dict[str, float] = {}


@worker_process_init.connect
def _start_metrics_server(**kwargs):
    if not settings.metrics.enabled:
        return

    try:
        start_http_server(settings.metrics.worker_metrics_port)
    except OSError:
        # Port already bound - with concurrency > 1 this fires for
        # every child process after the first; see module docstring.
        logger.info(
            "Worker metrics server not started on port %s (already in use).",
            settings.metrics.worker_metrics_port,
        )


@task_prerun.connect
def _record_task_start(task_id=None, **kwargs):
    if task_id is not None:
        _task_start_times[task_id] = time.perf_counter()


@task_postrun.connect
def _record_task_duration(task_id=None, task=None, **kwargs):
    start = _task_start_times.pop(task_id, None)
    if start is not None and task is not None:
        CELERY_TASK_DURATION_SECONDS.labels(task_name=task.name).observe(
            time.perf_counter() - start,
        )


@task_success.connect
def _record_task_success(sender=None, **kwargs):
    if sender is not None:
        CELERY_TASK_TOTAL.labels(task_name=sender.name, status="success").inc()


@task_failure.connect
def _record_task_failure(sender=None, **kwargs):
    if sender is not None:
        CELERY_TASK_TOTAL.labels(task_name=sender.name, status="failure").inc()
