import os

from celery import Celery
from celery.signals import setup_logging as celery_setup_logging_signal
from celery.signals import task_postrun, task_prerun
from kombu import Queue

from app.config.logging import setup_logging, task_context_var
from app.config.settings import settings

# Importing this registers the worker-side Prometheus metrics signal
# handlers (task success/failure/duration) - see that module's
# docstring for the multiprocess-metrics caveat.
import app.workers.metrics  # noqa: F401


celery_app = Celery(
    "ai_video",
    broker=os.getenv(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/0",
    ),
    backend=os.getenv(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/0",
    ),
    include=[
        "app.workers.video_processor",
    ],
)

celery_app.conf.update(
    task_track_started=True,

    # Acknowledge only after the task finishes (not on delivery), so
    # a worker that crashes mid-task gets its task redelivered rather
    # than silently losing it. Safe specifically because
    # ProcessingPipeline.run() only ever does real work after winning
    # an atomic PENDING -> RUNNING claim
    # (ProcessingJobRepository.claim_for_running) - a redelivered task
    # for an already-claimed/finished job is a guaranteed no-op
    # (ProcessingPipeline.run logs and returns), never a duplicate
    # video processing run.
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # See CelerySettings.broker_visibility_timeout's docstring - without
    # this, the Redis transport's default (3600s) is what actually
    # governs redelivery, regardless of task_acks_late's intent.
    broker_transport_options={
        "visibility_timeout": settings.celery.broker_visibility_timeout,
    },

    # One task fetched at a time per worker process by default - these
    # tasks run long (transcription/embedding/LLM calls can take
    # minutes), so a worker should not prefetch/hoard several before
    # finishing the first.
    worker_prefetch_multiplier=settings.celery.worker_prefetch_multiplier,

    # Recycle each worker process after N tasks, bounding memory
    # growth from repeatedly loading large AI models (Whisper/BGE-M3/
    # cross-encoder) in the same long-lived process.
    worker_max_tasks_per_child=settings.celery.worker_max_tasks_per_child,

    # Hard/soft time limits so a stuck task (e.g. a hung external
    # call) cannot occupy a worker slot forever. The soft limit raises
    # SoftTimeLimitExceeded inside the task first; the hard limit
    # kills the worker process if that isn't handled in time.
    task_time_limit=settings.celery.task_time_limit,
    task_soft_time_limit=settings.celery.task_soft_time_limit,

    # Keep retrying to reach the broker on worker startup instead of
    # crashing immediately if Redis isn't up yet (e.g. Compose
    # dependency startup ordering) - a future Celery major version
    # defaults this to True; set explicitly for the installed version.
    broker_connection_retry_on_startup=True,

    # "celery_cpu"/"celery_gpu" are declared so a deployment with a
    # GPU-equipped worker fleet can route process_video there (start
    # that worker with `-Q celery_gpu` and WHISPER_DEVICE=cuda) purely
    # through configuration - see settings.celery.task_queue and
    # CelerySettings' docstring. There is currently only one
    # monolithic task covering the whole pipeline (transcription +
    # summary + embedding + translation + quiz/chapter/flashcard), so
    # this routes the *entire* job to one queue, not per-stage; finer
    # per-stage GPU/CPU routing would require splitting that task,
    # which is a business-logic change out of scope for this phase.
    task_queues=(
        Queue("celery_cpu"),
        Queue("celery_gpu"),
    ),
    task_default_queue=settings.celery.task_queue,
    task_routes={
        "app.workers.video_processor.process_video": {
            "queue": settings.celery.task_queue,
        },
    },
)


@celery_setup_logging_signal.connect
def _configure_worker_logging(**kwargs):
    """
    Take over Celery's own logging setup so worker processes use the
    same formatter/level/context-filter as the FastAPI process (see
    app.config.logging) instead of Celery's default handlers.
    """
    setup_logging()


@task_prerun.connect
def _set_task_log_context(task_id=None, task=None, **kwargs):
    task_context_var.set(
        {
            "task_name": task.name if task else None,
            "task_id": task_id,
        }
    )


@task_postrun.connect
def _clear_task_log_context(**kwargs):
    task_context_var.set(None)
