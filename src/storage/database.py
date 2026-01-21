"""Database connection management and initialization."""

from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.storage.models import Base

# Default database path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEFAULT_DB_PATH = DATA_DIR / "scholarships.db"

# Module-level engine and session factory
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine(db_path: Path | None = None) -> Engine:
    """Get or create the SQLAlchemy engine.

    Args:
        db_path: Optional path to the database file. Defaults to data/scholarships.db.

    Returns:
        SQLAlchemy Engine instance.
    """
    global _engine

    if _engine is None:
        if db_path is None:
            db_path = DEFAULT_DB_PATH

        # Ensure data directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        _engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,
            connect_args={"check_same_thread": False},
        )

    return _engine


def get_session() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        SQLAlchemy Session instance.
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())

    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(db_path: Path | None = None) -> None:
    """Initialize the database by creating all tables.

    Args:
        db_path: Optional path to the database file. Defaults to data/scholarships.db.
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
