import logging
import subprocess

logger = logging.getLogger(__name__)

# Downscaled at generation time (not read time) so the Library page
# never has to fetch/decode a full-resolution frame just to show a
# small card image - `-1` keeps the source aspect ratio.
THUMBNAIL_WIDTH = 640

# A hung/corrupt input must not occupy a Celery worker slot forever -
# this stage already runs inside the pipeline's own outer task time
# limit, but a per-call bound here fails fast and specifically,
# instead of relying only on that much longer outer limit.
FFMPEG_TIMEOUT_SECONDS = 30


def extract_thumbnail(file_path: str, duration: int) -> bytes | None:
    """
    Extract one representative JPEG frame from a video via ffmpeg
    (the same tool this project's transcription/metadata pipeline
    already shells out to - see app/utils/ffprobe.py, app/utils/
    audio.py). Seeks to roughly the first third of the video, clamped
    to at most 2s in, rather than frame 0 - real footage's first frame
    is often black or a title card, so this is a materially better
    representative frame with no added cost.

    Never raises. A corrupt file, a non-seekable stream, a video too
    short to seek into, or ffmpeg simply not being available all
    result in a logged warning and `None` - thumbnail extraction is a
    best-effort enhancement to the pipeline, not a required stage (see
    VideoPipelineService.metadata_stage, which treats a `None` return
    as "no thumbnail this run" and continues processing normally).
    """
    seek_seconds = min(2.0, duration / 3) if duration > 0 else 0.0

    command = [
        "ffmpeg",
        "-ss", f"{seek_seconds:.2f}",
        "-i", file_path,
        "-frames:v", "1",
        "-vf", f"scale={THUMBNAIL_WIDTH}:-1",
        "-q:v", "4",
        "-f", "image2",
        "-vcodec", "mjpeg",
        "pipe:1",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            check=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as error:
        logger.warning(
            "Thumbnail extraction failed for %s (seek=%.2fs): %s",
            file_path,
            seek_seconds,
            error,
        )
        return None

    if not result.stdout:
        logger.warning(
            "Thumbnail extraction produced no output for %s (seek=%.2fs)",
            file_path,
            seek_seconds,
        )
        return None

    return result.stdout
