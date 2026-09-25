"""
Upload validation helpers for POST /videos/upload.

Kept deliberately small and dependency-free (no python-magic/libmagic
addition) - extension allowlisting plus a streamed size cap, which
closes the actual gaps identified for this endpoint (arbitrary
filename used as a filesystem path, no extension/size limit) without
introducing new infrastructure.
"""
import re
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config.settings import settings

# Anything outside this allowlist is collapsed to "_". Deliberately
# conservative (no "..", "/", "\", NUL, or shell-special characters
# can survive), while still allowing normal filenames through mostly
# unchanged.
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """
    Reduce a client-supplied filename to a safe basename before it is
    ever used to build a filesystem path.

    `Path(filename).name` drops any directory component a crafted
    filename might carry (e.g. "../../etc/passwd" or an absolute
    path), and the character allowlist removes anything else that
    could be used to escape the intended upload directory or inject
    shell/filesystem-special characters. The result is never empty.
    """
    name = Path(filename or "").name
    name = name.strip().strip(".")

    if not name:
        name = "upload"

    return _UNSAFE_CHARS.sub("_", name)


def validate_upload_extension(filename: str) -> None:
    """
    Reject a file whose extension is not in
    settings.storage.allowed_upload_extensions. Raises 415, matching
    the fact that the client sent a representation the server does
    not support.
    """
    extension = Path(filename).suffix.lower()
    allowed = settings.storage.allowed_upload_extensions

    if extension not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported file type '{extension or '(none)'}'. "
                f"Allowed: {', '.join(allowed)}"
            ),
        )


def save_upload_within_limit(
    file: UploadFile,
    destination: Path,
    chunk_size: int = 1024 * 1024,
) -> int:
    """
    Stream `file` to `destination` in fixed-size chunks, enforcing
    settings.storage.max_upload_size_mb without ever holding the
    whole upload in memory.

    Raises 413 and removes the partially-written file the moment the
    limit is exceeded, so a client cannot exhaust disk space by
    uploading an oversized file regardless of what (if anything) its
    Content-Length header claimed. Returns the number of bytes
    written on success.
    """
    max_bytes = settings.storage.max_upload_size_mb * 1024 * 1024
    written = 0

    try:
        with destination.open("wb") as buffer:
            while True:
                chunk = file.file.read(chunk_size)

                if not chunk:
                    break

                written += len(chunk)

                if written > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                        detail=(
                            "File exceeds the maximum upload size of "
                            f"{settings.storage.max_upload_size_mb} MB."
                        ),
                    )

                buffer.write(chunk)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise

    return written
