# Development Guide

## Code Style

This project follows strict coding standards to ensure code quality and maintainability.

### Import Guidelines

- **No wildcard imports**: Always explicitly import each class, function, or variable.
  ```python
  # Good
  from module import ClassA, ClassB, function_a
  
  # Bad - Do not use
  from module import *
  ```

- **Import order**: 
  1. Standard library imports
  2. Third-party imports 
  3. Local application imports

### Type Annotations

- All function parameters and return values must be typed
- Use the modern type annotation syntax:
  ```python
  # Good
  def get_items() -> list[Item]:
      ...
  
  # Good
  def get_user(id: int | None = None) -> User | None:
      ...
  
  # Bad - Do not use
  from typing import List, Optional
  def get_items() -> List[Item]:
      ...
  def get_user(id: Optional[int] = None) -> Optional[User]:
      ...
  ```
- Run mypy regularly to ensure type correctness

### Error Handling

- Use structured exception handling
- Create custom exceptions for domain-specific errors
- Never silence exceptions without proper handling

### Asynchronous Code

- All database operations should be async
- Use proper async patterns and avoid blocking operations
- Never mix sync and async code without explicit conversion

### Testing

- All public functions and methods should have corresponding tests
- Use pytest fixtures to maintain DRY principles in tests
- Mock external services and APIs to ensure deterministic tests

### Documentation

- All modules, classes, and functions should have docstrings
- Include type information in docstrings
- Document parameters and return values

## Database Guidelines

- Use SQLModel for all database models
- Define relationships explicitly
- Use migrations for all schema changes
- Implement proper indexing strategy

## API Guidelines

- Follow RESTful principles
- Use appropriate HTTP methods and status codes
- Validate all inputs using Pydantic models
- Include detailed error responses

## LLM Integration Guidelines

- Isolate LLM-specific code in the infrastructure layer
- Create well-defined interfaces for LLM services
- Implement proper error handling for API failures
- Cache expensive operations where appropriate