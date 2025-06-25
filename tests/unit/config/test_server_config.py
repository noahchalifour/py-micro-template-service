from pydantic import ValidationError
import os
import pytest

from py_micro.service.config import ServerConfig


class TestServerConfig:
    """Test cases for ServerConfig."""

    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = ServerConfig()

        assert config.host == "0.0.0.0"
        assert config.port == 50051
        assert config.max_workers == 10
        assert config.grace_period == 30

    def test_environment_variables(self):
        """Test that environment variables override defaults."""
        os.environ["SERVER_HOST"] = "127.0.0.1"
        os.environ["SERVER_PORT"] = "8080"
        os.environ["SERVER_MAX_WORKERS"] = "20"
        os.environ["SERVER_GRACE_PERIOD"] = "60"

        config = ServerConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 8080
        assert config.max_workers == 20
        assert config.grace_period == 60

    def test_invalid_port(self):
        """Test validation of invalid port values."""
        os.environ["SERVER_PORT"] = "invalid"

        with pytest.raises(ValidationError):
            ServerConfig()

    def test_negative_values(self):
        """Test validation of negative values."""
        os.environ["SERVER_MAX_WORKERS"] = "-1"

        with pytest.raises(ValidationError):
            ServerConfig()
