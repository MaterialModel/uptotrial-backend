"""API entry point."""

import uvicorn

from uptotrial.app import create_app
from uptotrial.core.config import get_settings

app = create_app(get_settings())

if __name__ == "__main__":
    uvicorn.run(
        "uptotrial.main:app",
        host="0.0.0.0",
        port=8000,
        reload=get_settings().debug,
        workers=1,
    )