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

    `Path(...).name` drops any directory component a crafted filename
    might carry (e.g. "../../etc/passwd" or an absolute path), and the
    character allowlist removes anything else that could be used to
    escape the intended upload directory or inject shell/filesystem-
    special characters. The result is never empty.

    Backslashes are normalized to "/" first: this server runs on
    POSIX, where `pathlib.Path` does not treat "\\" as a separator, so
    a client-supplied Windows-style path (e.g.
    "C:\\Windows\\System32\\evil.mp4") would otherwise survive
    `Path(...).name` intact and only get its separators collapsed to
    "_" by the character allowlist below, instead of having its
    directory component stripped like every other path style.
    """
    name = (filename or "").replace("\\", "/")
    name = Path(name).name
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


# First bytes that identify a real container of each supported type,
# independent of whatever extension/Content-Type the client claims.
# Deliberately NOT a full MIME-sniffing library (no python-magic/
# libmagic dependency, matching this module's existing "small,
# dependency-free" design) - just the well-known container signatures
# for exactly the 6 extensions this app already allows, so a renamed
# non-video file never reaches the ffmpeg/ffprobe subprocess calls
# that follow upload. mp4/mov/m4v share the ISOBMFF "ftyp" box at
# offset 4; mkv/webm are both EBML-based and share an identical
# container-level signature (WebM is formally a Matroska profile) -
# distinguishing them further would require parsing the EBML DocType,
# which isn't needed here since both are already allowed extensions.
_CONTAINER_SIGNATURES: dict[str, tuple[bytes, ...]] = {
    ".mp4": (b"ftyp",),
    ".mov": (b"ftyp",),
    ".m4v": (b"ftyp",),
    ".mkv": (b"\x1a\x45\xdf\xa3",),
    ".webm": (b"\x1a\x45\xdf\xa3",),
    ".avi": (b"RIFF",),
}

SIGNATURE_PEEK_BYTES = 16


def validate_upload_signature(filename: str, header: bytes) -> None:
    """
    Reject a file whose actual leading bytes don't match a real
    container for its claimed extension - e.g. a text file or
    arbitrary binary blob renamed to ".mp4" to reach the ffmpeg/
    ffprobe subprocess calls this endpoint makes right after upload.

    `header` must be read from the start of the file (at least
    SIGNATURE_PEEK_BYTES long where possible) BEFORE any of it is
    written to disk or passed to those tools. Raises 415, matching
    validate_upload_extension's existing behavior for an unsupported
    type - from the client's perspective this is the same class of
    rejection, just caught one layer deeper.
    """
    extension = Path(filename).suffix.lower()
    signatures = _CONTAINER_SIGNATURES.get(extension)

    if signatures is None:
        # Extension itself isn't recognized - validate_upload_extension
        # (called first, at the route level) already rejects this
        # case; nothing further to check here.
        return

    if extension == ".avi":
        # RIFF container: "RIFF" at offset 0, then a 4-byte chunk
        # size, then the form type "AVI " at offset 8.
        is_valid = header[0:4] == b"RIFF" and header[8:12] == b"AVI "
    elif extension in (".mp4", ".mov", ".m4v"):
        is_valid = header[4:8] == b"ftyp"
    else:
        is_valid = any(
            header.startswith(signature) for signature in signatures
        )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"File content does not match a valid '{extension}' "
                f"video container."
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
