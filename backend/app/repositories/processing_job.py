from datetime import datetime, timedelta, UTC

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.processing_job import ProcessingJob
from app.models.processing_stage import ProcessingStage
from app.models.video import Video
from app.repositories.base import BaseRepository


class ProcessingJobRepository(BaseRepository[ProcessingJob]):
    """Repository for ProcessingJob model."""

    def __init__(
        self,
        db: Session,
    ):
        super().__init__(
            db=db,
            model=ProcessingJob,
        )

    def get_by_video_id(
        self,
        video_id: int,
    ) -> list[ProcessingJob]:

        return (
            self.db.query(ProcessingJob)
            .filter(ProcessingJob.video_id == video_id)
            .all()
        )

    def get_by_owner(
        self,
        owner_id: int,
    ) -> list[ProcessingJob]:
        """
        All processing jobs belonging to videos owned by `owner_id`.

        ProcessingJob has no direct user/owner column - ownership is
        scoped through its video, joining Video.owner_id, the same
        way every other resource in this codebase (transcripts,
        summaries, quizzes, ...) is scoped via VideoService.get_video's
        ownership check.
        """

        return (
            self.db.query(ProcessingJob)
            .join(Video, ProcessingJob.video_id == Video.id)
            .filter(Video.owner_id == owner_id)
            .all()
        )

    def get_by_id_and_owner(
        self,
        job_id: int,
        owner_id: int,
    ) -> ProcessingJob | None:
        """Single job, only if it belongs to a video owned by `owner_id`."""

        return (
            self.db.query(ProcessingJob)
            .join(Video, ProcessingJob.video_id == Video.id)
            .filter(
                ProcessingJob.id == job_id,
                Video.owner_id == owner_id,
            )
            .first()
        )

    def get_by_status(
        self,
        status: str,
    ) -> list[ProcessingJob]:

        return (
            self.db.query(ProcessingJob)
            .filter(ProcessingJob.status == status)
            .all()
        )

    def get_by_job_type(
        self,
        job_type: str,
    ) -> list[ProcessingJob]:

        return (
            self.db.query(ProcessingJob)
            .filter(ProcessingJob.job_type == job_type)
            .all()
        )
    
    def update(
        self,
        job: ProcessingJob,
    ) -> ProcessingJob:
        self.db.commit()
        self.db.refresh(job)
        return job

    def claim_for_running(
        self,
        job_id: int,
        stale_after_seconds: int | None = None,
        heartbeat_timeout_seconds: int | None = None,
    ) -> ProcessingJob | None:
        """
        Atomically transition a job to RUNNING and stamp started_at,
        but only if it is still PENDING, or (when `stale_after_seconds`
        is given) if it is RUNNING but has been for longer than that
        many seconds.

        This is a single conditional UPDATE - the PENDING branch
        exactly as before, with an OR'd second branch added rather
        than a separate SELECT-then-UPDATE. If multiple callers race
        for the same job, the database's row-level locking on the
        UPDATE ensures only one of them can ever match the row and
        win; the others see 0 updated rows and get None back,
        signalling "already claimed elsewhere, skip".

        The stale-RUNNING branch exists for a real gap this closes: a
        worker that crashes *after* claiming a job (status already
        RUNNING) left that job permanently unclaimable before this -
        Celery's own task_reject_on_worker_lost redelivery would
        re-invoke this method, but the old PENDING-only WHERE clause
        rejected it every time, since the job was RUNNING, not
        PENDING, forever. See ProcessingJobService.start_if_pending
        for why task_time_limit is the safe threshold to pass here.

        With `heartbeat_timeout_seconds`, a RUNNING job counts as
        stale as soon as its heartbeat_at has been quiet for that long
        (the owning worker is gone) instead of waiting out the whole
        `stale_after_seconds`; a RUNNING row with no heartbeat at all
        (predates the column) still uses the started_at rule. Every
        successful claim stamps heartbeat_at, so the new owner starts
        out "alive".
        """

        now = datetime.now(UTC)

        conditions = [ProcessingJob.status == "PENDING"]

        if stale_after_seconds is not None:
            conditions.append(
                self._stale_running_condition(
                    now,
                    fallback_seconds=stale_after_seconds,
                    heartbeat_timeout_seconds=heartbeat_timeout_seconds,
                )
            )

        updated_rows = (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id,
                or_(*conditions),
            )
            .update(
                {
                    ProcessingJob.status: "RUNNING",
                    ProcessingJob.started_at: now,
                    ProcessingJob.heartbeat_at: now,
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        if updated_rows == 0:
            return None

        return self.get_by_id(job_id)
    
    def update_progress(
        self,
        job: ProcessingJob,
        progress: int,
        current_step: str,
        status: str | None = None,
    ) -> ProcessingJob:
        job.progress = progress
        job.current_step = current_step
        job.heartbeat_at = datetime.now(UTC)

        if status is not None:
            job.status = status

        self.db.commit()
        self.db.refresh(job)

        return job
    
    def get_by_id(
        self,
        job_id:int
    ):
        return (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id
            )
            .first()
        )

    def get_orphaned_pending(
        self,
        video_id: int,
        older_than_seconds: int,
    ) -> list[ProcessingJob]:
        """
        PENDING jobs for this video that have never been claimed
        (started_at is still NULL) and are older than the dispatch
        grace period - i.e. their original Celery dispatch likely
        never arrived (UploadPipeline.process's dual-write gap), not
        merely still in flight. Scoped to one video since every
        caller already has a specific video in hand (e.g. a
        processing-jobs read); a global sweep across all videos is
        intentionally not provided here - see
        scripts/reconcile_processing_jobs.py for that.
        """
        cutoff = datetime.now(UTC) - timedelta(
            seconds=older_than_seconds,
        )

        return (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.video_id == video_id,
                ProcessingJob.status == "PENDING",
                ProcessingJob.started_at.is_(None),
                ProcessingJob.created_at < cutoff,
            )
            .all()
        )

    def claim_for_retry(
        self,
        job_id: int,
    ) -> ProcessingJob | None:
        """
        Atomically transition a job FAILED -> PENDING for a manual,
        user-initiated retry (POST /processing-jobs/{id}/retry) - the
        only path that resets a terminal FAILED job back to
        something process_video can pick up again.

        Single conditional UPDATE, exactly mirroring claim_for_running
        and claim_for_dispatch_retry's shape: only a row currently
        FAILED matches, so two concurrent retry requests (e.g. a
        double click) can never both "win" - the second sees 0
        updated rows and gets None back, which the caller surfaces as
        a 409 rather than silently retrying twice.

        Clears progress/current_step/error_message/started_at/
        finished_at and resets dispatch_attempts to 1, so the job
        looks exactly like a freshly-created one to every downstream
        consumer (claim_for_running, the opportunistic orphaned-
        dispatch reconciliation, the API response) - no stale data
        from the previous failed attempt leaks through. Does NOT
        touch processing_stages: VideoPipelineService's existing
        per-stage resume logic (skip COMPLETED, retry FAILED/
        incomplete, bounded by ProcessingStageService.
        has_exhausted_retries) already does the right thing on the
        next run without any help from this method - that is the
        entire reason a job-level retry is sufficient here instead of
        needing its own stage-reset logic.
        """
        updated_rows = (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id,
                ProcessingJob.status == "FAILED",
            )
            .update(
                {
                    ProcessingJob.status: "PENDING",
                    ProcessingJob.progress: 0,
                    ProcessingJob.current_step: None,
                    ProcessingJob.error_message: None,
                    ProcessingJob.started_at: None,
                    ProcessingJob.finished_at: None,
                    ProcessingJob.dispatch_attempts: 1,
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        if updated_rows == 0:
            return None

        return self.get_by_id(job_id)

    def get_all_orphaned_pending(
        self,
        older_than_seconds: int,
        limit: int,
    ) -> list[ProcessingJob]:
        """
        Same eligibility as get_orphaned_pending, across every video
        rather than one - for scripts/reconcile_processing_jobs.py's
        operator-triggered sweep. The per-video read path
        (get_orphaned_pending, used by
        UploadPipeline.reconcile_orphaned_jobs) only ever looks at
        one video a caller already has in hand; this exists
        separately so that narrower, more frequently-hit path never
        pays for an unbounded table scan.
        """
        cutoff = datetime.now(UTC) - timedelta(
            seconds=older_than_seconds,
        )

        return (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.status == "PENDING",
                ProcessingJob.started_at.is_(None),
                ProcessingJob.created_at < cutoff,
            )
            .order_by(ProcessingJob.created_at.asc())
            .limit(limit)
            .all()
        )

    def claim_for_dispatch_retry(
        self,
        job_id: int,
    ) -> ProcessingJob | None:
        """
        Atomically increment dispatch_attempts for a job that is
        still PENDING and unclaimed (started_at IS NULL) - the same
        single-conditional-UPDATE pattern claim_for_running uses
        (see its own docstring), so that if two concurrent
        reconciliation attempts race for the same orphaned job (e.g.
        two browser tabs polling .../processing-jobs at once), at
        most one of them proceeds to actually call .delay() again.

        Returns None if the job was no longer eligible - already
        reconciled/started by a concurrent call, or already moved
        past PENDING by then. The caller should treat that as
        "already handled elsewhere" and skip, exactly like
        claim_for_running's own callers do.
        """
        updated_rows = (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id,
                ProcessingJob.status == "PENDING",
                ProcessingJob.started_at.is_(None),
            )
            .update(
                {
                    ProcessingJob.dispatch_attempts: (
                        ProcessingJob.dispatch_attempts + 1
                    ),
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        if updated_rows == 0:
            return None

        return self.get_by_id(job_id)

    @staticmethod
    def _stale_running_condition(
        now: datetime,
        fallback_seconds: int,
        heartbeat_timeout_seconds: int | None,
    ):
        """
        SQL condition for "RUNNING, but its worker is presumed dead".

        - With a heartbeat timeout: heartbeat_at older than that
          timeout, or - for a row with no heartbeat at all - started_at
          older than `fallback_seconds`.
        - Without one: the original started_at-only rule.
        """
        fallback_cutoff = now - timedelta(seconds=fallback_seconds)

        if heartbeat_timeout_seconds is None:
            return and_(
                ProcessingJob.status == "RUNNING",
                ProcessingJob.started_at < fallback_cutoff,
            )

        heartbeat_cutoff = now - timedelta(seconds=heartbeat_timeout_seconds)

        return and_(
            ProcessingJob.status == "RUNNING",
            or_(
                and_(
                    ProcessingJob.heartbeat_at.is_not(None),
                    ProcessingJob.heartbeat_at < heartbeat_cutoff,
                ),
                and_(
                    ProcessingJob.heartbeat_at.is_(None),
                    ProcessingJob.started_at < fallback_cutoff,
                ),
            ),
        )

    def touch_heartbeat(
        self,
        job_id: int,
    ) -> bool:
        """
        Refresh heartbeat_at for a job that is still RUNNING. Returns
        False once the job is no longer RUNNING (completed, failed,
        or marked interrupted), so the heartbeat loop can stop.
        """
        updated_rows = (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id,
                ProcessingJob.status == "RUNNING",
            )
            .update(
                {ProcessingJob.heartbeat_at: datetime.now(UTC)},
                synchronize_session=False,
            )
        )

        self.db.commit()

        return updated_rows > 0

    def get_stale_running(
        self,
        heartbeat_timeout_seconds: int,
        fallback_seconds: int,
        limit: int,
        video_id: int | None = None,
    ) -> list[ProcessingJob]:
        """
        RUNNING jobs whose worker is presumed dead (see
        _stale_running_condition), optionally for one video only.
        """
        query = self.db.query(ProcessingJob).filter(
            self._stale_running_condition(
                datetime.now(UTC),
                fallback_seconds=fallback_seconds,
                heartbeat_timeout_seconds=heartbeat_timeout_seconds,
            )
        )

        if video_id is not None:
            query = query.filter(ProcessingJob.video_id == video_id)

        return (
            query.order_by(ProcessingJob.started_at.asc())
            .limit(limit)
            .all()
        )

    def mark_interrupted(
        self,
        job_id: int,
        heartbeat_timeout_seconds: int,
        fallback_seconds: int,
        error: str,
    ) -> ProcessingJob | None:
        """
        Atomically move a stale RUNNING job to FAILED, and fail the
        stage it was in the middle of, in one transaction.

        The UPDATE re-checks staleness in its own WHERE clause, so a
        job whose worker sends a heartbeat between the caller's read
        and this write is left alone (0 rows, returns None) - a live
        job is never failed. Its RUNNING stage is failed too (not left
        RUNNING), otherwise a later retry could not claim that stage
        again until the full task_time_limit had passed.
        """
        now = datetime.now(UTC)

        updated_rows = (
            self.db.query(ProcessingJob)
            .filter(
                ProcessingJob.id == job_id,
                self._stale_running_condition(
                    now,
                    fallback_seconds=fallback_seconds,
                    heartbeat_timeout_seconds=heartbeat_timeout_seconds,
                ),
            )
            .update(
                {
                    ProcessingJob.status: "FAILED",
                    ProcessingJob.progress: 100,
                    ProcessingJob.current_step: "Failed",
                    ProcessingJob.error_message: error,
                    ProcessingJob.finished_at: now,
                },
                synchronize_session=False,
            )
        )

        if updated_rows == 0:
            self.db.rollback()
            return None

        (
            self.db.query(ProcessingStage)
            .filter(
                ProcessingStage.processing_job_id == job_id,
                ProcessingStage.status == "RUNNING",
            )
            .update(
                {
                    ProcessingStage.status: "FAILED",
                    ProcessingStage.finished_at: now,
                    ProcessingStage.error_message: error,
                },
                synchronize_session=False,
            )
        )

        self.db.commit()

        return self.get_by_id(job_id)
