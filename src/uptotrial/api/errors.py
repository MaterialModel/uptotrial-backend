"""Error handling utilities for API endpoints."""

from typing import Any, Dict

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


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
    if isinstance(exc, NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.detail},
        )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.detail},
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors.
    
    Args:
        request: FastAPI request
        exc: Validation error exception
        
    Returns:
        JSONResponse: Error response with validation details
    """
    errors: Dict[str, Any] = {"detail": []}
    
    for error in exc.errors():
        error_detail = {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"],
        }
        errors["detail"].append(error_detail)
    
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