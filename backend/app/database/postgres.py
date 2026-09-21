from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

# Pool sizing/recycling is environment-driven (settings.database.*)
# rather than hardcoded, so production can tune it without a code
# change; defaults match the pre-Phase-13 behavior (pool_pre_ping=True,
# with SQLAlchemy's own pool_size=5/max_overflow=10 defaults) closely
# enough to be a safe, backward-compatible starting point.
engine = create_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_timeout=settings.database.pool_timeout,
    pool_recycle=settings.database.pool_recycle,
    pool_pre_ping=settings.database.pool_pre_ping,
    echo=settings.database.echo,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)