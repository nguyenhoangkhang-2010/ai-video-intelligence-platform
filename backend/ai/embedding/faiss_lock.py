import logging
import os
import time
from pathlib import Path


logger = logging.getLogger(__name__)


class FileLock:
    """
    Minimal cross-platform advisory file lock used to serialize
    concurrent FAISS index/metadata writes across Celery workers.

    Uses os.open with O_CREAT|O_EXCL, which is an atomic "create if
    not exists" on both POSIX and Windows, so no extra dependency is
    required.
    """

    def __init__(
        self,
        lock_path: str | Path,
        timeout: float = 30.0,
        stale_after: float = 120.0,
        poll_interval: float = 0.05,
    ):
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self.stale_after = stale_after
        self.poll_interval = poll_interval
        self._fd: int | None = None

    def acquire(self) -> None:
        deadline = time.monotonic() + self.timeout

        while True:
            try:
                self._fd = os.open(
                    str(self.lock_path),
                    os.O_CREAT | os.O_EXCL | os.O_RDWR,
                )
                os.write(self._fd, str(os.getpid()).encode())
                return
            except FileExistsError:
                if self._is_stale():
                    self._force_release()
                    continue

                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Timed out acquiring FAISS store lock: {self.lock_path}"
                    )

                time.sleep(self.poll_interval)

    def release(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                self._fd = None

        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

    def _is_stale(self) -> bool:
        try:
            age = time.time() - self.lock_path.stat().st_mtime
        except FileNotFoundError:
            return False

        return age > self.stale_after

    def _force_release(self) -> None:
        try:
            self.lock_path.unlink()
            logger.warning(
                "Removed stale FAISS store lock: %s",
                self.lock_path,
            )
        except FileNotFoundError:
            pass

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
