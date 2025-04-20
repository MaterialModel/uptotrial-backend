"""Tests for the correlation ID middleware."""

import uuid

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from httpx import AsyncClient
from starlette import status

from src.uptotrial.api.middleware import CorrelationIdMiddleware


@pytest.fixture
def test_app() -> FastAPI:
    """Create a test application with correlation ID middleware."""
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    
    @app.get("/exempt")
    async def exempt_route():
        return {"message": "Exempt route"}
    
    @app.get("/protected")
    async def protected_route(request: Request):
        return {"message": "Protected route", "correlation_id": request.state.correlation_id}
    
    return app


@pytest.mark.asyncio
async def test_exempt_route_adds_correlation_id(test_app: FastAPI) -> None:
    """Test that exempt routes get a correlation ID automatically."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Modify the path to match one of the exempt paths
        response = await client.get("/api/health")
        
        assert response.status_code == status.HTTP_200_OK
        assert "X-Correlation-ID" in response.headers
        
        # Verify the correlation ID is a valid UUID
        correlation_id = response.headers["X-Correlation-ID"]
        assert uuid.UUID(correlation_id)


@pytest.mark.asyncio
async def test_protected_route_requires_correlation_id(test_app: FastAPI) -> None:
    """Test that protected routes require a correlation ID."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get("/protected")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "X-Correlation-ID header is required" in response.text


@pytest.mark.asyncio
async def test_protected_route_rejects_invalid_correlation_id(test_app: FastAPI) -> None:
    """Test that protected routes reject invalid correlation IDs."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get(
            "/protected", 
            headers={"X-Correlation-ID": "not-a-uuid"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "X-Correlation-ID must be a valid UUID" in response.text


@pytest.mark.asyncio
async def test_protected_route_accepts_valid_correlation_id(test_app: FastAPI) -> None:
    """Test that protected routes accept valid correlation IDs."""
    correlation_id = str(uuid.uuid4())
    
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        response = await client.get(
            "/protected", 
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["X-Correlation-ID"] == correlation_id
        
        # Verify the correlation ID is accessible in the route handler
        data = response.json()
        assert data["correlation_id"] == correlation_id