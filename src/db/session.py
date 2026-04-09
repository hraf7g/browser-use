from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.shared.config.settings import get_settings


def build_database_url() -> str:
    """Build and validate the database URL from application settings."""
    settings = get_settings()
    database_url = settings.database_url.strip()
    if not database_url:
        raise ValueError("database_url must not be empty")
    return database_url

@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Create and cache the shared SQLAlchemy engine."""
    return create_engine(
        build_database_url(),
        pool_pre_ping=True,
        echo=False,
    )

@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Create and cache the shared SQLAlchemy session factory."""
    return sessionmaker(
        bind=get_engine(),
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session and ensure it is closed."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()