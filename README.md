# UpToTrial - Clinical Trials Search API

A FastAPI-based API that enables natural language search on ClinicalTrials.gov data using Large Language Models (LLMs) and the OpenAI Responses API.

## Project Overview

UpToTrial leverages LLMs to understand search intent and context beyond basic keyword matching, providing a powerful search experience for clinical researchers and patients looking for suitable clinical trials.

For detailed project requirements, see the [Product Requirements Document](prds/2025-04-19-Fastapi-Clinical-Trials-Search.md).

### Key Features

- **Natural Language Search**: Use everyday language to find clinical trials
- **LLM Integration**: Powered by OpenAI's Responses API for conversational search
- **Domain-Driven Design**: Clean architecture for maintainability and scalability
- **Fully Async**: Built with FastAPI and async Python for high performance
- **Correlation ID**: Request tracing with enforced correlation IDs
- **Rate Limiting**: Two-tier rate limiting (global and per-correlation-ID)
- **Type-Safe**: Fully type-annotated with modern Python 3.12+ syntax
- **CLI Tool**: Command-line interface for direct trial searches

## Technical Stack

- **FastAPI**: Web framework for building APIs
- **SQLModel**: ORM for database interactions combining SQLAlchemy and Pydantic
- **Pydantic**: Data validation and settings management
- **PostgreSQL**: Primary database
- **Alembic**: Database migration tool
- **OpenAI Responses API**: LLM integration for natural language understanding
- **Typer**: CLI framework for command-line tool
- **Pytest & Tox**: Testing framework and orchestration
- **Ruff & Mypy**: Linting and type checking

## Project Structure

The project follows a domain-driven design approach with a clean architecture. For details on the structure and architecture principles, see [Project Structure Guide](.cursor/rules/01-project-structure.mdc).

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- OpenAI API key

### Local Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/uptotrial-backend.git
   cd uptotrial-backend
   ```

2. **Set up a virtual environment with Python 3.12 using uv**

   ```bash
   # Install uv if you don't have it
   pip install uv
   
   # Create virtual environment with Python 3.12
   uv venv .venv --python=3.12
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. **Install dependencies using uv**

   ```bash
   # Install project dependencies
   uv pip install -e ".[dev]"
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root by copying `.env.example`:

   ```bash
   cp .env.example .env
   ```

   Then edit the file to set your OpenAI API key and other configurations.

5. **Set up the database**

   ```bash
   # Create PostgreSQL database
   createdb uptotrial

   # Run migrations (this will prompt for confirmation)
   alembic upgrade head
   ```

6. **Run the development server**

   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API documentation**

   Open your browser and navigate to:
   - Swagger UI: http://localhost:8000/docs
   - API Root: http://localhost:8000/

### Environment Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development, testing, staging, production) | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/uptotrial` |
| `OPENAI_API_KEY` | OpenAI API key | ` ` |
| `OPENAI_MODEL` | OpenAI model name | `gpt-4o` |
| `GLOBAL_RATE_LIMIT_REQUESTS` | Global rate limit per minute | `60` |
| `CORRELATION_ID_RATE_LIMIT_REQUESTS` | Per-correlation-ID rate limit per minute | `30` |

## Development Guidelines

### Code Style

This project follows strict coding standards for maintainability and consistency. For details, see:

- [Code Style Guide](.cursor/rules/02-code-style.mdc) - Type annotations, imports, and more
- [Development Standards](docs/development_guide.md) - Comprehensive coding standards

### API Development

When developing API endpoints, follow the guidelines in:
- [API Guidelines](.cursor/rules/03-api-guidelines.mdc) - Endpoint structure and best practices

### Correlation IDs

UpToTrial requires correlation IDs for request tracking and security:

```bash
curl -X GET "http://localhost:8000/api/v1/search?query=cancer" \
     -H "X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000"
```

For details on working with correlation IDs, see:
- [Correlation ID Documentation](docs/correlation_id.md)
- [Correlation ID Guidelines](.cursor/rules/06-correlation-id.mdc)

### LLM Integration

For details on working with the OpenAI Responses API, see:
- [Responses API Documentation](docs/responses_api.md)
- [LLM Integration Guidelines](.cursor/rules/04-llm-integration.mdc)

## Testing

The project uses Tox for test orchestration and Pytest for testing. The tox configuration is in `pyproject.toml` and specifically requires Python 3.12. Always run tests through Tox:

```bash
# Run all tests with Python 3.12
tox

# Run only linting
tox -e lint

# Run only type checking
tox -e typecheck

# Run tests with coverage reporting
tox -e coverage

# Run specific tests
tox -e specific -- tests/unit/test_middleware/test_correlation_id.py -v

# Using python -m syntax (alternative)
python -m tox -e lint
```

For detailed testing guidelines, see [Testing Guidelines](.cursor/rules/05-testing.mdc).

## CLI Usage

The project includes a CLI for searching clinical trials:

```bash
# Show help
uptotrial --help

# Show current version
uptotrial version

# Display configuration
uptotrial config

# Search for trials
uptotrial search "breast cancer trials for women over 50 in New York"
```

## Database Migrations

Alembic is used for database migrations with safety features:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations (will prompt for confirmation)
alembic upgrade head

# Run non-interactively (for CI/CD)
ALEMBIC_NON_INTERACTIVE=1 alembic upgrade head
```

The migration system includes database identification to prevent accidental migrations on production.

## Continuous Integration

GitHub Actions runs the CI pipeline on every push and pull request. The workflow performs:
- Tests against a PostgreSQL instance
- Code formatting and linting checks
- Type annotation verification
- Integration tests

## Documentation

- [Development Guide](docs/development_guide.md) - Comprehensive coding standards
- [Correlation ID](docs/correlation_id.md) - Correlation ID implementation details
- [Responses API](docs/responses_api.md) - OpenAI Responses API integration
- [CLAUDE.md](CLAUDE.md) - Guidelines for Claude when working with this codebase

## Copyright

© 2025 UpToTrial. All rights reserved. This codebase and its contents are proprietary and confidential.