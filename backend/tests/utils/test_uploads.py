from io import BytesIO
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.utils.uploads import (
    sanitize_filename,
    save_upload_within_limit,
    validate_upload_extension,
)


# ---- sanitize_filename ----

def test_sanitize_filename_leaves_a_normal_filename_unchanged():
    assert sanitize_filename("clip.mp4") == "clip.mp4"


def test_sanitize_filename_strips_directory_traversal():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("../../../etc/shadow.mp4") == "shadow.mp4"


def test_sanitize_filename_strips_absolute_path():
    assert sanitize_filename("/etc/passwd") == "passwd"
    assert sanitize_filename("C:\\Windows\\System32\\evil.mp4") == "evil.mp4"


def test_sanitize_filename_replaces_unsafe_characters():
    result = sanitize_filename("my video (final)!.mp4")
    assert "/" not in result
    assert " " not in result
    assert "(" not in result
    assert result.endswith(".mp4")


def test_sanitize_filename_never_returns_empty():
    assert sanitize_filename("") != ""
    assert sanitize_filename("...") != ""
    assert sanitize_filename("../../") != ""


# ---- validate_upload_extension ----

def test_validate_upload_extension_accepts_allowed_extension():
    validate_upload_extension("clip.mp4")  # does not raise


def test_validate_upload_extension_rejects_disallowed_extension():
    with pytest.raises(HTTPException) as exc_info:
        validate_upload_extension("payload.exe")

    assert exc_info.value.status_code == 415


def test_validate_upload_extension_rejects_missing_extension():
    with pytest.raises(HTTPException) as exc_info:
        validate_upload_extension("noextension")

    assert exc_info.value.status_code == 415


# ---- save_upload_within_limit ----

def _make_upload_file(data: bytes):
    upload = MagicMock(name="upload_file")
    upload.file = BytesIO(data)
    return upload


def test_save_upload_within_limit_writes_all_bytes(tmp_path):
    destination = tmp_path / "out.mp4"
    upload = _make_upload_file(b"hello video bytes")

    written = save_upload_within_limit(upload, destination, chunk_size=4)

    assert written == len(b"hello video bytes")
    assert destination.read_bytes() == b"hello video bytes"


def test_save_upload_within_limit_rejects_oversized_upload_and_cleans_up(tmp_path):
    destination = tmp_path / "out.mp4"
    upload = _make_upload_file(b"x" * 100)

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr(
            "app.utils.uploads.settings.storage.max_upload_size_mb",
            50 / (1024 * 1024),
        )

        with pytest.raises(HTTPException) as exc_info:
            save_upload_within_limit(upload, destination, chunk_size=10)

    assert exc_info.value.status_code == 413
    assert not destination.exists()
