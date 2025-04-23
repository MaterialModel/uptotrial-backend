"""Database session management."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

DeclarativeBase = declarative_base()


async def inject_db() -> AsyncIterator[AsyncSession]:

    @asynccontextmanager
    async def _get_db() -> AsyncIterator[AsyncSession]:
        db = async_session_maker()

        if not isinstance(db, AsyncSession):
            raise TypeError(f"Expected AsyncSession, got {type(db)}")

        try:
            yield db
            await db.commit()
        except Exception as e:
            await asyncio.shield(db.rollback())
            logger.error(f"Error in database transaction, rolling back: {e}")
            raise
        finally:
            await db.close()

    async with _get_db() as db:
        yield db