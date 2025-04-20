"""Application configuration settings."""

import re
from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "UpToTrial API"
    app_description: str = "Clinical Trials Search API"
    app_version: str = "0.1.0"
    environment: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False

    # API
    api_prefix: str = "/api"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/uptotrial",
        description="Database connection string",
    )
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o", description="OpenAI model to use")

    # Security
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    rate_limit_period_seconds: int = 60  # Time window for rate limiting
    global_rate_limit_requests: int = 60  # Global requests per IP per period
    correlation_id_rate_limit_requests: int = 30  # Requests per correlation ID per period
    
    @computed_field
    def database_identifier(self) -> str:
        """Get a human-readable identifier for the current database.
        
        Returns:
            str: A string identifying the database being used (e.g., "PRODUCTION - mydatabase@hostname")
        """
        # Extract database name, hostname, and username from the database URL
        pattern = r".*://(?P<username>[^:]+)(?::.*)?@(?P<hostname>[^:/]+)(?::\d+)?/(?P<database>.+)"
        match = re.match(pattern, self.database_url)
        
        if match:
            db_name = match.group("database")
            hostname = match.group("hostname")
            username = match.group("username")
            return f"{self.environment.upper()} - {db_name}@{hostname} (user: {username})"
        
        # Fallback if regex doesn't match
        return f"{self.environment.upper()} - {self.database_url}"


@lru_cache
def get_settings() -> Settings:
    """Create cached settings instance."""
    return Settings()