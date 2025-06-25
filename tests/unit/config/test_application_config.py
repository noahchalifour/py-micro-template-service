import os

from py_micro.service.config import ApplicationConfig, ServerConfig, LoggingConfig


class TestApplicationConfig:
    """Test cases for main ApplicationConfig class."""

    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = ApplicationConfig()

        assert config.app_name == "py-micro-service"
        assert config.version == "0.1.0"
        assert config.debug is False
        assert config.environment == "development"

        # Test nested configurations
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_nested_environment_variables(self):
        """Test that nested environment variables work correctly."""
        os.environ["APP_NAME"] = "test-service"
        os.environ["DEBUG"] = "true"
        os.environ["ENVIRONMENT"] = "production"
        os.environ["SERVER__HOST"] = "localhost"
        os.environ["SERVER__PORT"] = "9090"
        os.environ["LOGGING__LEVEL"] = "ERROR"

        config = ApplicationConfig()

        assert config.app_name == "test-service"
        assert config.debug is True
        assert config.environment == "production"
        assert config.server.host == "localhost"
        assert config.server.port == 9090
        assert config.logging.level == "ERROR"

    def test_case_insensitive_environment_variables(self):
        """Test that environment variables are case insensitive."""
        os.environ["app_name"] = "case-test"
        os.environ["DEBUG"] = "True"

        config = ApplicationConfig()

        assert config.app_name == "case-test"
        assert config.debug is True

    def test_boolean_environment_variables(self):
        """Test various boolean value formats in environment variables."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
        ]

        for env_value, expected in test_cases:
            os.environ["DEBUG"] = env_value
            config = ApplicationConfig()
            assert config.debug == expected, f"Failed for env_value: {env_value}"

    def test_extra_fields_ignored(self):
        """Test that extra fields in environment are ignored."""
        os.environ["UNKNOWN_FIELD"] = "should_be_ignored"

        # Should not raise an exception
        config = ApplicationConfig()
        assert not hasattr(config, "unknown_field")

    def test_config_initialization_with_kwargs(self):
        """Test configuration initialization with keyword arguments."""
        config = ApplicationConfig(
            app_name="custom-app",
            version="1.0.0",
            debug=True,
        )

        assert config.app_name == "custom-app"
        assert config.version == "1.0.0"
        assert config.debug is True

    def test_config_repr(self):
        """Test configuration string representation."""
        config = ApplicationConfig(app_name="test-app")
        repr_str = repr(config)

        assert "Config" in repr_str
        assert "test-app" in repr_str
