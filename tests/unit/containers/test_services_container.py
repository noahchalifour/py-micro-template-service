from dependency_injector import providers

from py_micro.service.containers import ApplicationContainer, ServicesContainer
from py_micro.service.services import TemplateService


class TestServicesContainer:
    """Test cases for ServicesContainer."""

    def test_container_initialization(self):
        """Test that ServicesContainer initializes correctly."""
        container = ServicesContainer()

        # Test that providers are configured
        assert isinstance(container.config, providers.Configuration)
        assert isinstance(container.template_service, providers.Factory)

    def test_template_service_provider_with_dependencies(self):
        """Test that template service provider works with dependencies."""
        # Create application container
        app_container = ApplicationContainer()
        services_container = app_container.services

        # Get template service
        template_service = services_container.template_service()

        assert isinstance(template_service, TemplateService)
