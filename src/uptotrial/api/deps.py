"""Dependency injection functions for API endpoints."""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from uptotrial.core.config import Settings, get_settings
from uptotrial.infrastructure.database.session import get_db_session


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
    async with get_db_session() as session:
        yield session