"""
Test configuration for pytest.

This module provides common fixtures and utilities for testing.
"""

import os
from py_micro.service.config.server_config import ServerConfig
import pytest
from unittest.mock import Mock, MagicMock
from dependency_injector import providers
import structlog

from py_micro.service.config import ApplicationConfig
from py_micro.service.containers import ApplicationContainer


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=structlog.BoundLogger)
    logger.bind.return_value = logger
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return ApplicationConfig(
        app_name="test-app",
        version="0.1.0",
        debug=True,
        environment="test",
    )


@pytest.fixture
def test_server_config():
    """Create a test server configuration."""
    return ServerConfig().model_dump()


@pytest.fixture
def container():
    """Create a test container with mocked dependencies."""
    container = ApplicationContainer()

    # Override logger with mock
    container.logger.override(providers.Object(Mock(spec=structlog.BoundLogger)))

    return container


@pytest.fixture(autouse=True)
def clean_environment():
    """Clean environment variables before each test."""
    # Store original environment
    original_env = dict(os.environ)

    # Clean test-related environment variables
    test_env_vars = [
        "SERVER_HOST",
        "SERVER_PORT",
        "SERVER_MAX_WORKERS",
        "SERVER_GRACE_PERIOD",
        "LOGGING_LEVEL",
        "LOGGING_FORMAT",
        "DATABASE_URL",
        "DATABASE_POOL_SIZE",
        "DATABASE_MAX_OVERFLOW",
    ]

    for var in test_env_vars:
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def grpc_context():
    """Create a mock gRPC context for testing."""
    context = Mock()
    context.set_code = Mock()
    context.set_details = Mock()
    return context
