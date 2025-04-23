"""Database package."""

from app.infrastructure.database.session import inject_db

__all__ = ["inject_db"]
