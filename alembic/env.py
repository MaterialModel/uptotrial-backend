"""Alembic environment configuration."""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from alembic.config import Config
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.uptotrial.core.config import get_settings  # noqa: E402
from src.uptotrial.infrastructure.database.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get application settings
settings = get_settings()

# Set database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata


def confirm_migration(database_id: str) -> bool:
    """Ask for confirmation before running migrations.
    
    Args:
        database_id: Database identifier string
        
    Returns:
        bool: True if confirmed, False otherwise
    """
    print("\n" + "=" * 80)
    print(f"You are about to run migrations on:\n\n\033[1;33m{database_id}\033[0m\n")
    
    # Check for non-interactive mode
    if os.environ.get("ALEMBIC_NON_INTERACTIVE", "").lower() in ("1", "true", "yes"):
        print("Non-interactive mode detected. Proceeding without confirmation.")
        return True
    
    # Add special warning for production
    if settings.environment.lower() == "production":
        print("\033[1;31m!!! WARNING: This is a PRODUCTION database !!!\033[0m")
        confirm = input("\nAre you ABSOLUTELY SURE you want to proceed? [y/N]: ")
        return confirm.lower() == "y"
    else:
        confirm = input("\nDo you want to proceed? [Y/n]: ")
        return confirm.lower() != "n"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    
    # Confirm migration
    if not confirm_migration(settings.database_identifier):
        print("Migration cancelled.")
        return
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in 'online' mode."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Confirm migration
    if not confirm_migration(settings.database_identifier):
        print("Migration cancelled.")
        return
    
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())