from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RepositoryConfig(BaseSettings):
    """Repository configuration settings."""

    class_path: str = Field(
        default="modelrepo.repository.InMemoryModelRepository",
        description="Class path for the model repository to use.",
    )
    args: dict = Field(
        default={},
        description="Arguments to pass to the model repository class.",
    )

    model_config = SettingsConfigDict(env_prefix="REPOSITORY_")
