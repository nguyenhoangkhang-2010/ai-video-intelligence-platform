from sqlalchemy.orm import sessionmaker

from app.database.postgres import engine

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)