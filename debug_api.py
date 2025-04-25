"""This file is a convenient entry point for running the application in debug mode."""

import asyncio
import warnings

import uvicorn

from app import create_app
from app.config import get_settings

settings = get_settings()

def main() -> None:
    """Entry point for running the application in debug mode."""

    # Enable asyncio debug mode
    asyncio.get_event_loop().set_debug(True)

    # Enable RuntimeWarnings for unawaited coroutines
    warnings.simplefilter("always", RuntimeWarning)

    # Run the FastAPI application
    uvicorn.run(create_app(settings=settings), host="localhost", port=8000, log_level="debug")


if __name__ == "__main__":
    main()
