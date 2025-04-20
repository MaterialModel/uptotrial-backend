"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from app import __version__

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    version: str


@router.get(
    "",
    response_model=HealthResponse,
    responses={
        200: {"description": "Health check successful"},
        500: {"description": "Server is not healthy"},
    },
)
async def health_check() -> HealthResponse:
    """Perform a health check.

    Returns:
        HealthResponse: Health status response.
    """
    return HealthResponse(status="ok", version=__version__)