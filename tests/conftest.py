"""Pytest configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

from src.uptotrial.app import create_app
from src.uptotrial.core.config import Settings, get_settings
from src.uptotrial.infrastructure.database.session import get_db_session


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


class TestSettings(Settings):
    """Test settings override."""
    
    environment: str = "testing"
    debug: bool = True
    database_url: str = os.environ.get(
        "TEST_DATABASE_URL", 
        "postgresql+psycopg://postgres:postgres@localhost:5432/uptotrial_test"
    )


@pytest.fixture(scope="session")
def test_settings() -> TestSettings:
    """Test settings fixture."""
    return TestSettings()


@pytest_asyncio.fixture(scope="session")
async def db_engine(test_settings: TestSettings) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database engine."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with get_db_session() as session:
        yield session


@pytest.fixture
def app(test_settings: TestSettings) -> FastAPI:
    """Create a test application."""
    return create_app(test_settings)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the application."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client