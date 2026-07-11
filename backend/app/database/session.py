from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.database.postgres import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

def get_db():
    """Create and close a database session for each request."""

    db: Session = SessionLocal()

    try:
        yield db
    finally:
        db.close()