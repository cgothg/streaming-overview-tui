from pathlib import Path

from platformdirs import user_data_dir
from sqlmodel import create_engine
from sqlmodel import Session
from sqlmodel import SQLModel

APP_NAME = "streaming-overview-tui"
DATA_DIR = Path(user_data_dir(APP_NAME))
DATABASE_FILE = DATA_DIR / "cache.db"

# Create engine lazily
_engine = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{DATABASE_FILE}")
    return _engine


def init_db() -> None:
    """Initialize the database, creating tables if needed."""
    from streaming_overview_tui.data_layer.models import CachedMovie  # noqa: F401
    from streaming_overview_tui.data_layer.models import CachedShow  # noqa: F401
    from streaming_overview_tui.data_layer.models import (
        StreamingAvailability,  # noqa: F401
    )

    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    engine = get_engine()
    return Session(engine)
