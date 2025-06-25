"""
Configuration module for the py_micro.service.

This module provides configuration management using Pydantic settings,
allowing configuration from environment variables, files, and defaults.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .server_config import ServerConfig
from .logging_config import LoggingConfig


class ApplicationConfig(BaseSettings):
    """Main application configuration."""

    app_name: str = Field(default="py-micro-service", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment name")

    # Nested configurations
    server: ServerConfig = Field(default_factory=ServerConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )
