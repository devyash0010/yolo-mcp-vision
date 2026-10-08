"""Database engine and session management with PostgreSQL and SQLite support."""

import os
import asyncio
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger
from app.database.models import Base

# Sync engine & sessionmaker using built-in sqlite3 / psycopg2
_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL
        # Normalize URL for standard SQLAlchemy engine
        if "+aiosqlite" in db_url:
            db_url = db_url.replace("+aiosqlite", "")
        elif "+asyncpg" in db_url:
            db_url = db_url.replace("+asyncpg", "")

        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        logger.info("Initializing database engine: %s", db_url.split("@")[-1])
        _engine = create_engine(
            db_url,
            echo=settings.DATABASE_ECHO,
            connect_args=connect_args,
        )
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        eng = get_engine()
        _session_factory = sessionmaker(
            bind=eng,
            expire_on_commit=False,
            autoflush=False,
        )
    return _session_factory


class AsyncSessionWrapper:
    """Provides async session interface over standard SQLAlchemy session."""

    def __init__(self, sync_session: Session):
        self._sync_session = sync_session

    def add(self, instance):
        self._sync_session.add(instance)

    async def flush(self):
        await asyncio.to_thread(self._sync_session.flush)

    async def commit(self):
        await asyncio.to_thread(self._sync_session.commit)

    async def rollback(self):
        await asyncio.to_thread(self._sync_session.rollback)

    async def close(self):
        await asyncio.to_thread(self._sync_session.close)

    async def execute(self, statement):
        return await asyncio.to_thread(self._sync_session.execute, statement)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self.close()


class AsyncSessionFactoryWrapper:
    def __init__(self, factory):
        self._factory = factory

    def __call__(self) -> AsyncSessionWrapper:
        return AsyncSessionWrapper(self._factory())


async def init_db() -> None:
    """Creates database tables if they do not exist."""
    try:
        eng = get_engine()
        await asyncio.to_thread(Base.metadata.create_all, eng)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning("Database initialization notice: %s", str(e))


def get_async_session_factory():
    return AsyncSessionFactoryWrapper(get_session_factory())


async def get_db():
    """FastAPI dependency yielding an async database session wrapper."""
    factory = get_async_session_factory()
    session = factory()
    async with session:
        yield session

