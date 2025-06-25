from dependency_injector import containers, providers
import structlog

from py_micro.service.config import ApplicationConfig

from .services_container import ServicesContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """
    Main dependency injection container.

    This container orchestrates all other containers and provides the main
    entry point for dependency injection throughout the application.
    """

    # Configuration
    config = providers.Configuration(pydantic_settings=[ApplicationConfig()])

    # Wiring configuration - defines which modules should be wired for DI
    wiring_config = containers.WiringConfiguration(
        modules=[
            "py_micro.service.main",
            "py_micro.service.services.template_service",
        ]
    )

    # Logging factory
    logger_factory = providers.Factory(structlog.get_logger)

    # Main application logger
    logger = providers.Singleton(
        logger_factory,
        name=config.app_name,
    )

    # Services container
    services = providers.Container(ServicesContainer, config=config.services)
