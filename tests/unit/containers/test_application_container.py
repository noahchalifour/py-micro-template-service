from dependency_injector import providers, containers

from py_micro.service.containers import ApplicationContainer


class TestApplicationContainer:
    """Test cases for ApplicationContainer."""

    def test_container_initialization(self):
        """Test that ApplicationContainer initializes correctly."""
        container = ApplicationContainer()

        # Test that providers are configured
        assert isinstance(container.config, providers.Configuration)
        assert isinstance(container.wiring_config, containers.WiringConfiguration)
        assert isinstance(container.logger_factory, providers.Factory)
        assert isinstance(container.logger, providers.Singleton)
        assert isinstance(container.services, providers.Container)

    def test_config_provider(self):
        """Test that config provider returns dictionary."""
        container = ApplicationContainer()
        config = container.config()

        assert isinstance(config, dict)

    def test_logger_provider(self):
        """Test that logger provider returns logger instance."""
        container = ApplicationContainer()
        logger = container.logger()

        assert logger is not None
        # The actual logger type may vary based on structlog configuration

    def test_logger_factory_provider(self):
        """Test that logger factory provider creates loggers."""
        container = ApplicationContainer()
        logger = container.logger_factory()

        assert logger is not None
