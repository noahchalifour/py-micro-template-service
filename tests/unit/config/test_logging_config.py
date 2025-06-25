import os

from py_micro.service.config import LoggingConfig


class TestLoggingConfig:
    """Test cases for LoggingConfig."""

    def test_default_values(self):
        """Test that default logging configuration values are set correctly."""
        config = LoggingConfig()

        assert config.level == "INFO"
        assert config.format == "json"

    def test_environment_variables(self):
        """Test that environment variables override defaults."""
        os.environ["LOGGING_LEVEL"] = "DEBUG"
        os.environ["LOGGING_FORMAT"] = "console"

        config = LoggingConfig()

        assert config.level == "DEBUG"
        assert config.format == "console"
