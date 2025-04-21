# UpToTrial Backend

FastAPI-based API for clinical trials search using natural language processing.

## Project Overview

UpToTrial is a modern API service designed to provide advanced search capabilities for clinical trials data. The system leverages OpenAI's Responses API to enable natural language understanding and processing of clinical trial related queries.

Key features:
- Natural language search of clinical trials data
- Conversation context preservation
- Structured JSON or human-readable text responses
- Rate-limited API to ensure service stability
- Request correlation for tracking and debugging

## Technology Stack

- **Framework**: FastAPI (Python 3.12+)
- **Database**: SQLAlchemy with async support
- **LLM Integration**: OpenAI Responses API
- **Documentation**: Swagger UI (OpenAPI)
- **Testing**: pytest with async support
- **Code quality**: ruff, mypy
- **CI/CD**: tox-based test automation

## Getting Started

### Prerequisites

- Python 3.12+
- uv (https://github.com/astral-sh/uv)

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/uptotrial-backend.git
cd uptotrial-backend
```

2. Install `uv`

```bash
pip install uv
```

3. Create a virtual environment and install dependencies
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Configuration

The application uses environment variables for configuration. Create a `.env` file based on .env.example

### Running the Application

```bash
# Development server with auto-reload
uvicorn app.main:app --reload

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### CLI

```bash

 python ./uptotrial.py --help

 ```
 
## API Documentation

Once the application is running, access the API documentation at:
- http://localhost:8000/docs - Interactive Swagger UI

### Key Endpoints

- `GET /api/health` - Health check endpoint (no authentication needed)

### Authentication

Most endpoints require a valid `X-Correlation-ID` header containing a UUID to track and rate-limit requests. Example:

```
X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000
```

The health check endpoint is exempt from this requirement.

## Development

### Testing

```bash
# Run all tests, linting, and type checking
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

### Auto-fixing with ruff

```
ruff check --fix .
```

### Database Migrations

The project uses Alembic for database schema migrations:

```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## License

This project is licensed under proprietary terms.

## Contributing

Please follow the coding standards outlined in the project documentation and ensure all tests pass before submitting pull requests.

## Development Guidelines

For detailed development standards, refer to the following guidelines:

- [Project Structure and Architecture](.cursor/rules/01-project-structure.mdc)
- [Code Style and Formatting](.cursor/rules/02-code-style.mdc)
- [API Development Guidelines](.cursor/rules/03-api-guidelines.mdc)
- [Testing Guidelines](.cursor/rules/04-testing.mdc)