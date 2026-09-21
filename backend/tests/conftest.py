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
