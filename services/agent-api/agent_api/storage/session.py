from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agent_api.settings import get_settings
from agent_api.storage.models import Base


def create_sync_engine():
    return create_engine(get_settings().database_url, pool_pre_ping=True)


engine = create_sync_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_all() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
