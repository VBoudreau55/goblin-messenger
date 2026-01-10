"""Database configuration and session management."""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from goblin_messenger.models import Webhook  # noqa: F401

DB_PATH = Path.home() / ".goblin-messenger" / "webhooks.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    """Initialize the database by creating all tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a database session."""
    return Session(engine)
