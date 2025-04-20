"""Base models for database tables."""

import uuid
from datetime import datetime

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel


class Base(SQLModel, table=False):
    """Base model for all database tables."""

    id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        ),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime | None = Field(default=None, nullable=True)