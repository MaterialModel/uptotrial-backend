"""Test fixtures for integration tests."""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.app import create_app
from app.config import get_settings


@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Create a FastAPI app instance for testing."""
    test_settings = get_settings()
    return create_app(test_settings)


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create an AsyncClient for testing the FastAPI application."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
