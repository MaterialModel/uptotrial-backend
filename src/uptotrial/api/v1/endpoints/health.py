"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from uptotrial import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Perform a health check.

    Returns:
        HealthResponse: Health status response.
    """
    return HealthResponse(status="ok", version=__version__)