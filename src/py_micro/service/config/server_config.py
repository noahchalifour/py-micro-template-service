from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    """Server configuration settings."""

    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=50051, description="Server port number")
    max_workers: int = Field(
        default=10, gt=0, description="Maximum number of worker threads"
    )
    grace_period: int = Field(
        default=30, description="Graceful shutdown period in seconds"
    )

    model_config = SettingsConfigDict(env_prefix="SERVER_")
