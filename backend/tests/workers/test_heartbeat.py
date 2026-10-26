import threading
import time
from unittest.mock import MagicMock, patch

from app.workers.heartbeat import JobHeartbeat
from app.workers import recovery


def test_heartbeat_ticks_while_work_runs_and_stops_afterwards():
    touches = []

    def touch():
        touches.append(time.monotonic())
        return True

    with JobHeartbeat(touch, job_id=1, interval_seconds=0.02):
        time.sleep(0.15)

    count_at_exit = len(touches)
    time.sleep(0.08)

    assert count_at_exit >= 3
    assert len(touches) == count_at_exit  # no ticks after the block ends


def test_heartbeat_stops_on_its_own_once_the_job_is_no_longer_running():
    calls = []

    def touch():
        calls.append(1)
        return False  # job finished / was marked interrupted elsewhere

    with JobHeartbeat(touch, job_id=1, interval_seconds=0.02):
        time.sleep(0.12)

    assert len(calls) == 1


def test_a_failing_touch_is_retried_and_never_raised():
    attempts = []

    def touch():
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("database briefly unavailable")
        return True

    with JobHeartbeat(touch, job_id=1, interval_seconds=0.02):
        time.sleep(0.12)

    assert len(attempts) >= 2


def test_heartbeat_thread_is_a_daemon_so_it_never_blocks_worker_shutdown():
    heartbeat = JobHeartbeat(lambda: True, job_id=7, interval_seconds=10)

    assert heartbeat._thread.daemon is True
    assert heartbeat._thread.name == "job-heartbeat-7"


def test_worker_ready_sweeps_now_and_again_after_the_heartbeat_timeout():
    with (
        patch.object(recovery, "recover_stale_jobs", return_value=2) as sweep,
        patch.object(threading, "Timer") as timer_cls,
    ):
        recovery._recover_on_worker_ready()

    sweep.assert_called_once()
    timer_cls.assert_called_once()
    timer = timer_cls.return_value
    assert timer.daemon is True
    timer.start.assert_called_once()


def test_worker_ready_survives_a_failing_sweep():
    with (
        patch.object(recovery, "recover_stale_jobs", side_effect=RuntimeError("db down")),
        patch.object(threading, "Timer", MagicMock()),
    ):
        recovery._recover_on_worker_ready()  # must not raise
