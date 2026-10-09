"""
Sweep every video (not just one a user happens to be viewing) for
processing jobs whose original Celery dispatch likely never arrived -
UploadPipeline.process's dual-write gap: the ProcessingJob row is
committed, then process_video.delay() is called with no guard; if
that call raises or the process dies between the two steps, the job
is left PENDING forever with no task behind it.

UploadPipeline.reconcile_orphaned_jobs already self-heals this
opportunistically, but only for a video someone is actively polling
(app.api.v1.endpoints.videos.get_processing_jobs). A video nobody has
viewed since it broke - like the two known orphaned jobs this gap
left behind (job 5 / video 5, job 13 / video 13, both created in
September, confirmed still PENDING with no started_at as of this
script being written) - is never touched by that path. This script
is the operator-triggered equivalent for exactly that case.

Deliberately bounded, not an automatic mass-reprocess:

    python scripts/reconcile_processing_jobs.py [--limit N] [--dry-run]

- `--limit` (default 50) caps how many jobs a single run touches.
- `--dry-run` lists the candidates (with how many dispatch attempts
  they've already had) without re-dispatching or changing anything.
- Each candidate still goes through the exact same bounded,
  idempotent, concurrency-safe path as the opportunistic one
  (ProcessingJobService.reconcile_orphaned_dispatch) - this script
  does not bypass or duplicate that logic, only finds candidates
  across every video instead of one.
- Safe to re-run: a job already reconciled, already FAILED (attempts
  exhausted), or no longer eligible for any other reason is simply
  not returned by the next run's query.
"""
import argparse
import logging

from app.config.settings import VIDEO_UPLOAD_DIR
from app.database.session import SessionLocal
from app.repositories.processing_job import ProcessingJobRepository
from app.repositories.video import VideoRepository
from app.services.processing_job import ProcessingJobService
from app.services.video import VideoService
from app.workers.video_processor import process_video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reconcile_processing_jobs")


def reconcile(limit: int, dry_run: bool) -> None:
    db = SessionLocal()

    try:
        processing_job_service = ProcessingJobService(
            ProcessingJobRepository(db),
        )
        video_service = VideoService(VideoRepository(db))

        candidates = processing_job_service.get_all_orphaned_pending_jobs(
            limit=limit,
        )

        if not candidates:
            logger.info(
                "No orphaned PENDING processing jobs found. Nothing to do.",
            )
            return

        logger.info(
            "Found %s orphaned PENDING job(s) (limit=%s).",
            len(candidates),
            limit,
        )

        if dry_run:
            for job in candidates:
                logger.info(
                    "[dry-run] would reconcile job %s (video_id=%s, "
                    "dispatch_attempts so far=%s, created_at=%s)",
                    job.id,
                    job.video_id,
                    job.dispatch_attempts,
                    job.created_at,
                )
            return

        reconciled = 0
        failed = 0

        for job in candidates:
            video = video_service.get_video_by_id(job.video_id)

            if video is None:
                logger.warning(
                    "Job %s: video %s no longer exists - marking failed.",
                    job.id,
                    job.video_id,
                )
                processing_job_service.fail_job(
                    job.id,
                    error=(
                        "Processing could not be started: the video "
                        "no longer exists."
                    ),
                )
                failed += 1
                continue

            video_path = str(VIDEO_UPLOAD_DIR / video.filename)

            result = processing_job_service.reconcile_orphaned_dispatch(
                job,
                dispatch=lambda jid=job.id, vid=job.video_id, vp=video_path: (
                    process_video.delay(jid, vid, vp)
                ),
            )

            if result.status == "FAILED":
                logger.info(
                    "Job %s: dispatch attempts exhausted, now FAILED.",
                    job.id,
                )
                failed += 1
            else:
                logger.info(
                    "Job %s: re-dispatched (attempt %s).",
                    job.id,
                    result.dispatch_attempts,
                )
                reconciled += 1

        logger.info(
            "Reconciliation complete: %s re-dispatched, %s failed "
            "(attempts exhausted or video missing), %s candidate(s) total.",
            reconciled,
            failed,
            len(candidates),
        )
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of jobs to reconcile in this run (default: 50).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List candidates without re-dispatching or changing anything.",
    )
    args = parser.parse_args()

    reconcile(limit=args.limit, dry_run=args.dry_run)
