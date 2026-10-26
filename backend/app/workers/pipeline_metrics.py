"""
Stage-level Prometheus metrics for the video-processing pipeline.

Lives in the Celery worker process, alongside app.workers.metrics'
generic Celery task metrics - see that module's docstring for the
multiprocess/registry caveat (worker concurrency=1 assumed), which
applies identically here: these metrics are recorded inside
VideoPipelineService.process(), which only ever runs inside a worker
process, never the FastAPI process.

Labels are deliberately limited to `stage` and `result` - never
job_id/video_id/user_id/filename/exception text. Those belong in logs
(see video_pipeline.py's stage_started/stage_completed/stage_failed/
stage_skipped log calls), not Prometheus label values, which must stay
low-cardinality to avoid an unbounded number of time series.
"""
import logging
import time
from contextlib import contextmanager

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

STAGE_EXECUTIONS_TOTAL = Counter(
    "video_pipeline_stage_executions_total",
    "Total video-processing stage executions, by stage and result.",
    ["stage", "result"],
)

# Buckets reflect this pipeline's real workload: metadata/thumbnail
# extraction finishes in seconds, LLM-backed stages (summary/
# translation/quiz/chapter/flashcard) typically take tens of seconds,
# transcription/embedding on a long video can run into minutes.
STAGE_DURATION_SECONDS = Histogram(
    "video_pipeline_stage_duration_seconds",
    "Video-processing stage execution duration in seconds, by stage.",
    ["stage"],
    buckets=(1, 5, 15, 30, 60, 120, 300, 600, 1800, 3600),
)

PIPELINE_COMPLETED_TOTAL = Counter(
    "video_pipeline_completed_total",
    "Total video-processing pipeline runs, by final outcome.",
    ["result"],
)

ACTIVE_STAGES = Gauge(
    "video_pipeline_active_stages",
    "Number of stage executions currently in progress, by stage.",
    ["stage"],
)


def _safe(action) -> None:
    """
    Run a single metric-recording call, never letting a Prometheus
    client error propagate into the pipeline - observability is
    best-effort (see module docstring), never a dependency of
    processing correctness.
    """
    try:
        action()
    except Exception:
        logger.warning(
            "Failed to record a pipeline metric; continuing processing.",
            exc_info=True,
        )


@contextmanager
def observe_stage(stage_name: str):
    """
    Wrap one stage execution ATTEMPT (the caller must only enter this
    context when the stage is actually about to run - never for a
    stage the orchestration loop is skipping/leaving PENDING, so
    duration is never recorded for work that never happened).

    Active-stage gauge is incremented on entry and ALWAYS decremented
    in a finally block, so an exception can never leave it stuck.
    Duration and the execution/result counter are recorded exactly
    once, in that same finally block, with the correct result
    ("success" or "failure") regardless of how the caller's code
    exits.
    """
    _safe(lambda: ACTIVE_STAGES.labels(stage=stage_name).inc())
    start = time.perf_counter()
    failed = False

    try:
        yield
    except Exception:
        failed = True
        raise
    finally:
        duration = time.perf_counter() - start
        result = "failure" if failed else "success"

        _safe(lambda: STAGE_DURATION_SECONDS.labels(stage=stage_name).observe(duration))
        _safe(lambda: STAGE_EXECUTIONS_TOTAL.labels(stage=stage_name, result=result).inc())
        _safe(lambda: ACTIVE_STAGES.labels(stage=stage_name).dec())


def record_skipped(stage_name: str) -> None:
    """
    Record a stage that was explicitly marked SKIPPED (not merely left
    PENDING because its dependency never succeeded - that case is not
    an execution at all and must not be recorded here).
    """
    _safe(
        lambda: STAGE_EXECUTIONS_TOTAL.labels(stage=stage_name, result="skipped").inc()
    )


def record_pipeline_outcome(result: str) -> None:
    """result: one of "success" / "failure" / "incomplete"."""
    _safe(lambda: PIPELINE_COMPLETED_TOTAL.labels(result=result).inc())
