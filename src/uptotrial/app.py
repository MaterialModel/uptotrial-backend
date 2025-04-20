"""FastAPI application factory."""

from fastapi import FastAPI

from uptotrial.api.errors import register_exception_handlers
from uptotrial.api.middleware import register_middleware
from uptotrial.api.v1.router import api_router
from uptotrial.core.config import Settings


def create_app(settings: Settings) -> FastAPI:
    """Create FastAPI application instance."""
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        redoc_url=None,
    )

    # Register middleware
    register_middleware(app)
    
    # Register exception handlers
    register_exception_handlers(app)

    # Include API router
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/")
    async def root():
        return {"message": "Welcome to UpToTrial API. See /docs for API documentation."}

    return app