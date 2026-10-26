import pytest

from app.storage.local import LocalFilesystemStorage


def test_save_and_read_round_trip(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)

    storage.save("videos/1/source.mp4", b"fake video bytes")

    assert storage.read("videos/1/source.mp4") == b"fake video bytes"


def test_save_creates_parent_directories(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)

    storage.save("a/b/c/file.bin", b"data")

    assert (tmp_path / "a" / "b" / "c" / "file.bin").exists()


def test_exists_true_after_save_false_otherwise(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)

    assert storage.exists("missing.txt") is False

    storage.save("present.txt", b"x")

    assert storage.exists("present.txt") is True


def test_delete_removes_file(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)
    storage.save("to_delete.txt", b"x")

    storage.delete("to_delete.txt")

    assert storage.exists("to_delete.txt") is False


def test_delete_is_a_no_op_for_missing_key(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)

    # Must not raise.
    storage.delete("never_existed.txt")


def test_save_rejects_keys_that_escape_the_root(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)

    with pytest.raises(ValueError):
        storage.save("../escape.txt", b"x")


def test_get_local_path_returns_real_path_after_save(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)
    storage.save("videos/clip.mp4", b"data")

    path = storage.get_local_path("videos/clip.mp4")

    assert path is not None
    assert path.read_bytes() == b"data"


def test_get_local_path_returns_none_when_key_missing(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)

    assert storage.get_local_path("missing.mp4") is None


def test_get_url_always_returns_none_for_local_backend(tmp_path):
    storage = LocalFilesystemStorage(root=tmp_path)
    storage.save("videos/clip.mp4", b"data")

    assert storage.get_url("videos/clip.mp4") is None
