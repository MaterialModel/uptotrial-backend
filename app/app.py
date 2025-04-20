"""FastAPI application factory."""

import logging

from fastapi import FastAPI

from app import __version__
from app.api.errors import register_exception_handlers
from app.api.middleware import register_middleware
from app.api.router import api_router
from app.config import Settings

logger = logging.getLogger(__name__)


def create_app(settings: Settings) -> FastAPI:
    """Create FastAPI application instance."""
    logger.info("Creating FastAPI application in %s environment", settings.environment)
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=__version__,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        redoc_url=None,
    )

    # Register middleware
    logger.debug("Registering middleware")
    register_middleware(app)
    
    # Register exception handlers
    logger.debug("Registering exception handlers")
    register_exception_handlers(app)

    # Include API router
    logger.debug("Including API router with prefix: %s", settings.api_prefix)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/")
    async def root() -> dict[str, str]:
        logger.debug("Root endpoint called")
        return {"message": "Welcome to UpToTrial API. See /docs for API documentation."}

    logger.info("FastAPI application created successfully")
    return app