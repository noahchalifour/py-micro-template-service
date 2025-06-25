"""
Tests for the dependency injection containers.

This module tests the container configuration, dependency resolution,
and wiring functionality.
"""

import pytest
from unittest.mock import Mock, patch
import structlog
from dependency_injector import providers

from py_micro.service.containers import (
    ApplicationContainer,
    ServiceContainer,
    Container,
    setup_logging,
)
from py_micro.service.config import Config
from py_micro.service.services.user_service import UserService


class TestContainer:
    """Test cases for main Container."""

    def test_container_initialization(self):
        """Test that main Container initializes correctly."""
        container = Container()

        # Test that sub-containers are configured
        assert isinstance(container.application, providers.Container)
        assert isinstance(container.services, providers.Container)

        # Test convenience providers
        assert container.config is container.application.config
        assert container.logger is container.application.logger
        assert container.user_service is container.services.user_service

    def test_wiring_configuration(self):
        """Test that wiring configuration is set correctly."""
        container = Container()

        assert hasattr(container, "wiring_config")
        assert "py_micro.service.main" in container.wiring_config.modules
        assert (
            "py_micro.service.services.user_service" in container.wiring_config.modules
        )

    def test_create_service_logger(self):
        """Test create_service_logger method."""
        container = Container()

        # Mock the logger factory
        mock_logger = Mock()
        mock_logger.bind.return_value = mock_logger
        container.application.logger_factory.override(
            providers.Object(lambda: mock_logger)
        )

        service_logger = container.create_service_logger("test_service")

        assert service_logger is not None
        mock_logger.bind.assert_called_once_with(service="test_service")

    def test_get_service_config(self):
        """Test get_service_config method."""
        container = Container()

        # Override config with test values
        test_config = Config(
            app_name="test-app",
            environment="test",
            debug=True,
        )
        container.config.override(providers.Object(test_config))

        service_config = container.get_service_config("test_service")

        assert service_config["service_name"] == "test_service"
        assert service_config["app_name"] == "test-app"
        assert service_config["environment"] == "test"
        assert service_config["debug"] is True

    def test_container_can_be_wired(self):
        """Test that container can be wired without errors."""
        container = Container()

        # This should not raise an exception
        try:
            container.wire(modules=["py_micro.service.main"])
        except Exception as e:
            # It's okay if the module can't be found in test environment
            if "No module named" not in str(e):
                raise
