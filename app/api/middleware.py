"""Middleware for API endpoints."""

import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation IDs for request tracking."""
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process the request and ensure it has a correlation ID.
        
        Args:
            request: FastAPI request
            call_next: Function to call next middleware
            
        Returns:
            Response: FastAPI response
            
        Raises:
            HTTPException: If a protected endpoint is called without a correlation ID
        """
        # Skip correlation ID check for certain paths
        exempt_paths = [
            "/api/health", 
            "/docs", 
            "/openapi.json", 
            "/", 
            "/favicon.ico",
        ]
        
        if any(request.url.path.startswith(path) for path in exempt_paths):
            # For exempt paths, we still add a correlation ID for tracking,
            # but we don't require it to be present in the request
            correlation_id = str(uuid.uuid4())
            request.state.correlation_id = correlation_id
            logger.debug("Generated correlation ID %s for exempt path %s", correlation_id, request.url.path)
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        
        # For all other paths, require a correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        
        if not correlation_id:
            # Return 400 Bad Request if correlation ID is missing
            logger.warning("Request to %s missing required X-Correlation-ID header", request.url.path)
            return Response(
                content='{"detail":"X-Correlation-ID header is required"}',
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json",
            )
        
        # Validate UUID format
        try:
            uuid.UUID(correlation_id)
        except ValueError:
            # Return 400 Bad Request if correlation ID is not a valid UUID
            logger.warning("Invalid X-Correlation-ID value: %s", correlation_id)
            return Response(
                content='{"detail":"X-Correlation-ID must be a valid UUID"}',
                status_code=status.HTTP_400_BAD_REQUEST,
                media_type="application/json",
            )
        
        # Store correlation ID in request state for access in route handlers
        request.state.correlation_id = correlation_id
        
        # Process the request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class RequestProcessingTimeMiddleware(BaseHTTPMiddleware):
    """Middleware to track request processing time."""
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process the request and track time.
        
        Args:
            request: FastAPI request
            call_next: Function to call next middleware
            
        Returns:
            Response: FastAPI response
        """
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to implement rate limiting."""
    
    def __init__(self, app: FastAPI) -> None:
        """Initialize the middleware.
        
        Args:
            app: FastAPI application
        """
        super().__init__(app)
        self.settings = get_settings()
        # In a production system, use Redis or another distributed cache for rate limiting
        self.global_rate_limit_data = {}
        self.correlation_id_rate_limit_data = {}
    
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process the request and apply rate limiting.
        
        Args:
            request: FastAPI request
            call_next: Function to call next middleware
            
        Returns:
            Response: FastAPI response
        """
        # Skip rate limiting for certain paths
        exempt_paths = ["/api/health", "/docs", "/openapi.json", "/", "/favicon.ico"]
        if any(request.url.path.startswith(path) for path in exempt_paths):
            return await call_next(request)
        
        now = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        # 1. Apply global rate limiting based on IP
        if self._is_rate_limited(client_ip, now, self.global_rate_limit_data, 
                               self.settings.global_rate_limit_requests):
            logger.warning("Global rate limit exceeded for IP: %s", client_ip)
            return self._create_rate_limit_response(
                self.global_rate_limit_data[client_ip]["timestamp"], 
                now,
                self.settings.rate_limit_period_seconds,
                "Global rate limit exceeded",
            )
        
        # 2. Apply correlation ID-based rate limiting if available
        if hasattr(request.state, "correlation_id"):
            correlation_id = request.state.correlation_id
            if self._is_rate_limited(correlation_id, now, self.correlation_id_rate_limit_data,
                                   self.settings.correlation_id_rate_limit_requests):
                logger.warning("Correlation ID rate limit exceeded for ID: %s", correlation_id)
                return self._create_rate_limit_response(
                    self.correlation_id_rate_limit_data[correlation_id]["timestamp"],
                    now,
                    self.settings.rate_limit_period_seconds,
                    "Correlation ID rate limit exceeded",
                )
        
        # Process the request
        return await call_next(request)
    
    def _is_rate_limited(
        self, key: str, now: float, rate_limit_data: dict, limit: int,
    ) -> bool:
        """Check if a key is rate limited.
        
        Args:
            key: The rate limiting key (IP or correlation ID)
            now: Current timestamp
            rate_limit_data: Rate limit tracking dictionary
            limit: Maximum requests allowed
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        # Clean up old data
        for k in list(rate_limit_data.keys()):
            if now - rate_limit_data[k]["timestamp"] > self.settings.rate_limit_period_seconds:
                del rate_limit_data[k]
        
        # Initialize or update rate limit data
        if key not in rate_limit_data:
            rate_limit_data[key] = {
                "count": 1,
                "timestamp": now,
            }
            return False
        # Update existing data
        if now - rate_limit_data[key]["timestamp"] > self.settings.rate_limit_period_seconds:
            # Reset if period has passed
            rate_limit_data[key] = {
                "count": 1,
                "timestamp": now,
            }
            return False
        # Increment count
        rate_limit_data[key]["count"] += 1

        # Check if rate limit exceeded
        return rate_limit_data[key]["count"] > limit
    
    def _create_rate_limit_response(
        self, timestamp: float, now: float, period: int, message: str,
    ) -> Response:
        """Create a rate limit exceeded response.
        
        Args:
            timestamp: When the rate limit period started
            now: Current timestamp
            period: Rate limit period in seconds
            message: Error message
            
        Returns:
            Response: HTTP 429 response
        """
        retry_after = max(1, int(period - (now - timestamp)))
        
        response = Response(
            content=f'{{"detail":"{message}"}}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            media_type="application/json",
        )
        response.headers["Retry-After"] = str(retry_after)
        return response


def register_middleware(app: FastAPI) -> None:
    """Register middleware with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Correlation ID middleware (must be first custom middleware)
    app.add_middleware(CorrelationIdMiddleware)
    
    # Request timing middleware
    app.add_middleware(RequestProcessingTimeMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware)