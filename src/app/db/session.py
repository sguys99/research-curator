"""Database session management."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url_str,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables. Use only for testing; prefer Alembic for migrations."""
    from app.db.models import Base

    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables. Use only for testing."""
    from app.db.models import Base

    Base.metadata.drop_all(bind=engine)
