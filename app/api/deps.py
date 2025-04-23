"""Dependency injection functions for API endpoints."""

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.infrastructure.database.session import create_db_session


async def get_settings_dep() -> Settings:
    """Dependency that returns application settings.
    
    Returns:
        Settings: Application settings
    """
    return get_settings()


async def get_db(settings: Settings = Depends(get_settings_dep)) -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields a database session.
    
    Args:
        settings: Application settings
        
    Yields:
        AsyncSession: Database session
    """
    async with create_db_session() as session:
        yield session