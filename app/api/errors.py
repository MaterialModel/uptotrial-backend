"""Error handling utilities for API endpoints."""

import logging
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database-related errors."""

    def __init__(self, detail: str = "Database error occurred") -> None:
        self.detail = detail
        super().__init__(self.detail)


class NotFoundError(DatabaseError):
    """Exception raised when a requested resource is not found."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail)


class ServiceError(Exception):
    """Base exception for service-related errors."""
    
    def __init__(self, detail: str = "Service error occurred") -> None:
        self.detail = detail
        super().__init__(self.detail)


class LLMError(ServiceError):
    """Exception raised when there's an error with the LLM service."""
    
    def __init__(self, detail: str = "Error communicating with LLM service") -> None:
        super().__init__(detail)


async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    """Handle service errors.
    
    Args:
        request: FastAPI request
        exc: Service error exception
        
    Returns:
        JSONResponse: Error response
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error("Service error: %s", exc.detail, extra={"correlation_id": correlation_id})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": exc.detail},
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle database errors.
    
    Args:
        request: FastAPI request
        exc: Database error exception
        
    Returns:
        JSONResponse: Error response
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    if isinstance(exc, NotFoundError):
        logger.info("Resource not found: %s", exc.detail, extra={"correlation_id": correlation_id})
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.detail},
        )
    
    logger.error("Database error: %s", exc.detail, extra={"correlation_id": correlation_id})
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail},
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    """Handle validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation error exception
        
    Returns:
        JSONResponse: Error response with validation details
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    errors: dict[str, Any] = {"detail": []}
    
    for error in exc.errors():
        error_detail = {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        errors["detail"].append(error_detail)
    
    # Log validation errors with correlation ID
    logger.warning(
        "Validation error for request to %s: %s", 
        request.url.path, 
        exc.errors(),
        extra={"correlation_id": correlation_id},
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=errors,
    )


def register_exception_handlers(app: Any) -> None:
    """Register exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(ServiceError, service_error_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)