from collections.abc import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    Create and close a database session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()