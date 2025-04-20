# Correlation ID

## Overview

The UpToTrial API implements correlation ID tracking as a core feature of the system. Correlation IDs provide a way to trace requests across different components and services, making debugging and monitoring easier.

## Implementation

### How It Works

1. **Mandatory for API Calls**: All non-exempt API endpoints require a valid correlation ID to be included in the request headers.

2. **Header Format**: Correlation IDs must be provided in the `X-Correlation-ID` header as a valid UUID (e.g., `X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000`).

3. **Validation Rules**:
   - The header must be present
   - The value must be a valid UUID
   - Requests without a valid correlation ID will be rejected with a 400 Bad Request response

4. **Request Flow**:
   - The correlation ID from the request is validated
   - It is stored in the request state for access by route handlers
   - The same correlation ID is included in the response headers

5. **Exempt Endpoints**: The following endpoints don't require a correlation ID (but will generate one if not provided):
   - `/api/health`
   - `/docs`
   - `/openapi.json`

### Rate Limiting

Rate limiting is applied at two levels:

1. **Global Rate Limiting**: Limits requests by IP address (default: 60 requests per minute)
2. **Correlation ID Rate Limiting**: Limits requests by correlation ID (default: 30 requests per minute)

This dual approach helps prevent abuse while allowing legitimate high-volume clients to distribute their requests across multiple correlation IDs.

## Using Correlation IDs

### Client Perspective

When making API requests, clients should:

1. Generate a unique UUID for each logical transaction
2. Include the UUID in the `X-Correlation-ID` header
3. Use the same correlation ID for related requests
4. Create a new correlation ID for unrelated requests

Example request:

```http
GET /api/v1/search HTTP/1.1
Host: api.uptotrial.com
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Server Perspective

Within the application code, you can access the correlation ID in route handlers:

```python
@router.get("/example")
async def example_route(request: Request):
    correlation_id = request.state.correlation_id
    # Use correlation_id for logging, tracing, etc.
    return {"message": "Example response"}
```

## Logging and Tracing

The correlation ID is automatically integrated with the logging system and should be included in all log entries to enable request tracing.

Example logging usage:

```python
logger.info(f"Processing search request", extra={"correlation_id": request.state.correlation_id})
```

## Benefits

- **Debugging**: Easily track requests across components
- **Monitoring**: Analyze performance and usage patterns
- **Troubleshooting**: Quickly identify issues by correlating logs
- **Rate Limiting**: Prevent abuse while supporting legitimate high-volume use
- **Client Identification**: Track client behavior without requiring authentication