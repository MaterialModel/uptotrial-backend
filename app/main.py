"""API entry point."""

import logging

import uvicorn

from app.app import create_app
from app.core.config import get_settings

logger = logging.getLogger(__name__)

app = create_app(get_settings())
logger.info("Application started")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=get_settings().debug,
        workers=1,
    )
