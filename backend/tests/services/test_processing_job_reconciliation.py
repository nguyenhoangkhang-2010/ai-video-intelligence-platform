from unittest.mock import MagicMock

from app.services.processing_job import ProcessingJobService


def _service_with_repository():
    repository = MagicMock(name="repository")
    return ProcessingJobService(repository), repository


def _job(dispatch_attempts: int = 1, job_id: int = 1):
    job = MagicMock(name="job")
    job.id = job_id
    job.dispatch_attempts = dispatch_attempts
    return job


def test_reconcile_orphaned_dispatch_calls_dispatch_and_returns_claimed_job():
    service, repository = _service_with_repository()
    job = _job(dispatch_attempts=1)
    claimed = _job(dispatch_attempts=2, job_id=job.id)
    repository.claim_for_dispatch_retry.return_value = claimed

    dispatch = MagicMock(name="dispatch")

    result = service.reconcile_orphaned_dispatch(job, dispatch=dispatch)

    repository.claim_for_dispatch_retry.assert_called_once_with(job.id)
    dispatch.assert_called_once()
    assert result is claimed


def test_reconcile_orphaned_dispatch_skips_a_job_already_handled_concurrently():
    """
    claim_for_dispatch_retry returning None means a concurrent caller
    (or the job's original, merely-delayed dispatch finally arriving)
    already claimed it - this must not call dispatch() at all, and
    must not fail the job either; it's not an error, just a no-op.
    """
    service, repository = _service_with_repository()
    job = _job(dispatch_attempts=1)
    repository.claim_for_dispatch_retry.return_value = None

    dispatch = MagicMock(name="dispatch")

    result = service.reconcile_orphaned_dispatch(job, dispatch=dispatch)

    dispatch.assert_not_called()
    repository.update.assert_not_called()
    assert result is job


def test_reconcile_orphaned_dispatch_fails_job_when_dispatch_itself_raises():
    service, repository = _service_with_repository()
    job = _job(dispatch_attempts=1)
    claimed = _job(dispatch_attempts=2, job_id=job.id)
    repository.claim_for_dispatch_retry.return_value = claimed
    repository.get_by_id.return_value = claimed
    repository.update.side_effect = lambda j: j

    dispatch = MagicMock(side_effect=RuntimeError("broker unreachable"))

    result = service.reconcile_orphaned_dispatch(job, dispatch=dispatch)

    assert result.status == "FAILED"
    assert "could not be started" in result.error_message
    assert "broker unreachable" in result.error_message


def test_reconcile_orphaned_dispatch_fails_job_once_attempts_exhausted_without_dispatching():
    """
    Bounded retries: once dispatch_attempts has already reached
    settings.celery.max_dispatch_attempts (default 3), this must fail
    the job outright and must NOT call dispatch() or
    claim_for_dispatch_retry() again - a permanently-undispatchable
    job (broker down) must reach a clean terminal state instead of
    being retried forever.
    """
    service, repository = _service_with_repository()
    job = _job(dispatch_attempts=3)
    repository.get_by_id.return_value = job
    repository.update.side_effect = lambda j: j

    dispatch = MagicMock(name="dispatch")

    result = service.reconcile_orphaned_dispatch(job, dispatch=dispatch)

    dispatch.assert_not_called()
    repository.claim_for_dispatch_retry.assert_not_called()
    assert result.status == "FAILED"
    assert "3 attempt(s)" in result.error_message
    assert "never picked up" in result.error_message


def test_get_orphaned_pending_jobs_delegates_with_configured_grace_period():
    service, repository = _service_with_repository()
    repository.get_orphaned_pending.return_value = ["job-a"]

    result = service.get_orphaned_pending_jobs(video_id=42)

    assert result == ["job-a"]
    call_kwargs = repository.get_orphaned_pending.call_args.kwargs
    assert call_kwargs["video_id"] == 42
    assert isinstance(call_kwargs["older_than_seconds"], int)
    assert call_kwargs["older_than_seconds"] > 0
