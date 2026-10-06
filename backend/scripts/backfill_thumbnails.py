"""
Backfill thumbnails for already-processed videos that have none.

Every video processed before the thumbnail feature existed (see
app/utils/thumbnail.py and VideoPipelineService.metadata_stage) has
`thumbnail_key IS NULL` forever, since extraction only runs as part of
that pipeline stage going forward. This script closes that gap for
existing rows using the exact same extraction/storage building blocks
the live pipeline uses - no separate thumbnail path, no AI generation.

Deliberately bounded, not an automatic mass-reprocess:

    python scripts/backfill_thumbnails.py [--limit N] [--dry-run]

- `--limit` (default 50) caps how many videos a single run touches -
  VideoRepository.get_processed_without_thumbnail() enforces this at
  the query level, not just in this script's loop.
- `--dry-run` lists the candidates without extracting/writing anything.
- Restartable: it only ever selects rows where thumbnail_key is still
  NULL, so re-running after a partial run (or a failure) naturally
  skips everything already backfilled - no separate progress/offset
  state needed.
- Non-destructive: a video this script can't produce a thumbnail for
  (missing file, ffmpeg failure, timeout) is logged and skipped,
  exactly like a failure during live processing - thumbnail_key simply
  stays NULL, never faked.
"""
import argparse
import logging

from app.database.session import SessionLocal
from app.repositories.video import VideoRepository
from app.services.video import VideoService
from app.storage.factory import get_storage_backend
from app.utils.thumbnail import extract_thumbnail

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill_thumbnails")


def _video_storage_key(filename: str) -> str:
    """Mirrors app/api/v1/endpoints/videos.py::_video_storage_key exactly."""
    return f"videos/{filename}"


def backfill(limit: int, dry_run: bool) -> None:
    db = SessionLocal()

    try:
        repository = VideoRepository(db)
        service = VideoService(repository)
        storage = get_storage_backend()

        candidates = repository.get_processed_without_thumbnail(limit=limit)

        if not candidates:
            logger.info("No processed videos are missing a thumbnail. Nothing to do.")
            return

        logger.info(
            "Found %s processed video(s) without a thumbnail (limit=%s).",
            len(candidates),
            limit,
        )

        if dry_run:
            for video in candidates:
                logger.info("[dry-run] would backfill video %s (%s)", video.id, video.title)
            return

        succeeded = 0
        skipped = 0

        for video in candidates:
            source_path = storage.get_local_path(_video_storage_key(video.filename))

            if source_path is None or not source_path.exists():
                logger.warning(
                    "Skipping video %s: source file not found in storage (filename=%s).",
                    video.id,
                    video.filename,
                )
                skipped += 1
                continue

            image_bytes = extract_thumbnail(str(source_path), video.duration)

            if image_bytes is None:
                logger.warning(
                    "Skipping video %s: thumbnail extraction failed.",
                    video.id,
                )
                skipped += 1
                continue

            key = f"thumbnails/{video.id}.jpg"
            storage.save(key, image_bytes)
            service.update_thumbnail(video_id=video.id, thumbnail_key=key)

            logger.info("Backfilled thumbnail for video %s (key=%s).", video.id, key)
            succeeded += 1

        logger.info(
            "Backfill complete: %s succeeded, %s skipped, %s candidate(s) total.",
            succeeded,
            skipped,
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
        help="Maximum number of videos to backfill in this run (default: 50).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List candidates without extracting or writing anything.",
    )
    args = parser.parse_args()

    backfill(limit=args.limit, dry_run=args.dry_run)
