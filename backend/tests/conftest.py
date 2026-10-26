import os

# Must run before the first import of app.config.settings (triggered
# transitively by the app.* imports below) - pydantic-settings reads
# real environment variables with higher precedence than .env, so this
# reliably disables the Redis-backed rate limiter (app/core/rate_limit.py)
# for the whole test process, never for the running api/celery
# containers themselves (their own env is untouched).
#
# Real bug this fixes: test_videos_upload.py's TestClient hits the
# real FastAPI app, which carries the real `rate_limit("upload", ...)`
# dependency pointed at the real Redis instance (see conftest module
# docstring below - there is no fake/in-memory Redis for these
# endpoint tests). Its counter is keyed only by client IP
# ("ratelimit:upload:testclient" - TestClient's fixed host) with a
# 1-hour TTL, so repeated suite runs within an hour accumulate across
# runs and eventually return 429 instead of each test's real expected
# status - reproduced live: a fresh `redis-cli GET
# ratelimit:upload:testclient` after a few back-to-back runs shows the
# counter sitting at the configured limit. This is a test-isolation
# gap, not a product bug - the rate limiter's own behavior already has
# dedicated, fully-isolated coverage in tests/core/test_rate_limit.py,
# which patches `settings.rate_limit.enabled` directly per test and so
# is unaffected by this process-wide default.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base

# Importing the models package registers every ORM model class on
# Base.metadata (app/models/__init__.py imports all of them). Without
# this, Base.metadata.create_all() below would only create tables for
# whatever models happen to already be imported by the test itself.
import app.models  # noqa: F401


@pytest.fixture
def db_session():
    """
    Isolated in-memory SQLite session for repository/service tests.

    Uses the project's real SQLAlchemy Base (app.database.base.Base)
    and real model classes, so repository code runs against the real
    schema - only the engine differs (in-memory SQLite instead of
    Postgres). No PostgreSQL, Redis, Docker, or any AI
    model/service is required.

    A fresh engine and schema are created for every test so tests
    never leak state into each other. StaticPool pins all connections
    from this engine to the same underlying SQLite connection, since
    a plain ":memory:" database is otherwise private to whichever
    connection created it.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
