from app.workers.celery_app import celery_app


def test_task_acks_late_enabled_for_crash_safe_redelivery():
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True


def test_broker_visibility_timeout_is_configured_below_the_redis_default():
    """
    task_acks_late's crash-redelivery guarantee is only real if the
    Redis transport's visibility_timeout is actually set - left unset,
    it silently falls back to Redis's own default (3600s), which is
    what "task_acks_late enabled" alone does NOT protect against. A
    crashed/restarted worker's in-flight task would otherwise stay
    invisible to every other worker for up to an hour - confirmed live
    against this project's own Celery/Redis deployment.
    """
    from app.config.settings import settings

    timeout = celery_app.conf.broker_transport_options["visibility_timeout"]

    assert timeout == settings.celery.broker_visibility_timeout
    assert 0 < timeout < 3600


def test_broker_connection_retry_on_startup_enabled():
    assert celery_app.conf.broker_connection_retry_on_startup is True


def test_process_video_routed_to_configured_default_queue():
    from app.config.settings import settings

    route = celery_app.conf.task_routes["app.workers.video_processor.process_video"]

    assert route["queue"] == settings.celery.task_queue
    assert celery_app.conf.task_default_queue == settings.celery.task_queue


def test_both_cpu_and_gpu_queues_are_declared():
    queue_names = {queue.name for queue in celery_app.conf.task_queues}

    assert queue_names == {"celery_cpu", "celery_gpu"}


def test_time_limits_are_configured_and_positive():
    assert celery_app.conf.task_time_limit > 0
    assert celery_app.conf.task_soft_time_limit > 0
    assert celery_app.conf.task_soft_time_limit <= celery_app.conf.task_time_limit


def test_worker_max_tasks_per_child_is_bounded():
    assert celery_app.conf.worker_max_tasks_per_child > 0


def test_process_video_task_has_bounded_retry_configuration():
    from app.core.retry import TRANSIENT_EXCEPTIONS
    from app.workers.video_processor import process_video

    assert process_video.autoretry_for == TRANSIENT_EXCEPTIONS
    assert process_video.retry_backoff is True
    assert process_video.max_retries > 0
