from datetime import datetime, timedelta, UTC

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.processing_job import ProcessingJob
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
        """

        now = datetime.now(UTC)

        conditions = [ProcessingJob.status == "PENDING"]

        if stale_after_seconds is not None:
            stale_cutoff = now - timedelta(seconds=stale_after_seconds)
            conditions.append(
                and_(
                    ProcessingJob.status == "RUNNING",
                    ProcessingJob.started_at < stale_cutoff,
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