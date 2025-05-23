# CLAUDE.md - Guidelines for Claude When Working with UpToTrial

This document provides essential guidance for Claude when assisting with the UpToTrial codebase. Following these guidelines will ensure consistency and quality in code development.

## Project Overview

UpToTrial is a FastAPI-based clinical trials search API that uses OpenAI's Responses API to provide natural language search capabilities. The system follows domain-driven design principles and is built with modern Python 3.12+ features.

## Key Commands to Run

Before submitting code changes, always run these commands to ensure quality:

```bash
# Run all tests, linting, and type checking (preferred)
tox

# Run only linting
tox -e lint

# Run only type checking
tox -e typecheck 

# Run tests with coverage reporting
tox -e coverage

# Run specific tests
tox -e specific -- tests/unit/test_middleware/test_correlation_id.py
```

Note: All tox environments are configured in `pyproject.toml` and require Python 3.12.

When database migrations are involved:

```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations (with confirmation)
alembic upgrade head
```

## Package Management

Always use uv for package management:

```bash
# Create virtual environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"

# Add a new package
uv pip install new-package
```

## Project Rules

The project contains detailed rules in `.mdc` files in the `.cursor/rules/` directory. Always reference these when working on the codebase:

1. [Project Structure and Architecture](.cursor/rules/01-project-structure.mdc)
2. [Code Style and Formatting](.cursor/rules/02-code-style.mdc)
3. [API Development Guidelines](.cursor/rules/03-api-guidelines.mdc)
4. [Testing Guidelines](.cursor/rules/04-testing.mdc)

## Coding Standards

### Type Annotations

Always use modern Python 3.12+ type annotations:

```python
# CORRECT
def get_items() -> list[Item]:
    ...

def get_user(id: int | None = None) -> User | None:
    ...

# INCORRECT - DO NOT USE
from typing import List, Optional
def get_items() -> List[Item]:
    ...
def get_user(id: Optional[int] = None) -> Optional[User]:
    ...
```

### Import Guidelines

- **No wildcard imports**: Always import specific components
- Import order: standard library → third-party packages → local modules
- Keep imports alphabetized within each section

### Function Structure

- All public functions must have comprehensive docstrings with parameter and return value descriptions
- Include type annotations for all parameters and return values
- Keep functions focused on a single responsibility
- Maximum function length: aim for under 50 lines

### API Development

- New endpoints must require correlation ID headers (except for health checks)
- Use dependency injection for database sessions and services
- Follow error handling patterns from existing code
- Always validate input data with Pydantic models

### Database Operations

- All database operations must be asynchronous
- Use SQLModel for database models
- Include proper indexes for query performance
- Create migrations for all schema changes

### Middleware

- Respect the correlation ID mechanism for all endpoints
- Consider rate limiting impacts when designing new endpoints
- Include appropriate error handling

### Testing Guidelines

- Write unit tests for all public functions
- Use pytest fixtures for shared test components
- Mock external services (especially OpenAI API)
- Include integration tests for API endpoints
- Verify correlation ID behavior in endpoint tests

## Project Structure

When adding new components, place them in the appropriate directories:

- API endpoints: `app/api/endpoints/`
- Database models: `app/infrastructure/database/models/`
- Services: `app/services/`
- LLM utilities: `app/infrastructure/llm/`

## External Service Integration

When working with the OpenAI Responses API:

- Follow error handling patterns for API failures
- Properly mock responses in tests
- Consider rate limits and timeout settings

## Common Fixes and Best Practices

### Rate Limiting

Requests are rate-limited both globally and per correlation ID:
- Global: 60 requests per minute per IP
- Per correlation ID: 30 requests per minute

### Correlation ID Requirements

- All endpoints (except health checks and docs) require an X-Correlation-ID header
- Correlation ID must be a valid UUID
- Example header: `X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000`

### Database Migrations

- Always confirm which database is being migrated
- Development migrations will prompt for confirmation
- Production migrations require explicit confirmation
- CI/CD migrations use `ALEMBIC_NON_INTERACTIVE=1`

### Error Handling

- Use custom exception classes from `app/api/errors.py`
- Return appropriate HTTP status codes
- Include error details in the response
- Log errors with correlation IDs
