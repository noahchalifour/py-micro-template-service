from dependency_injector import containers, providers

from py_micro.service.services import TemplateService


class ServicesContainer(containers.DeclarativeContainer):
    """
    Services dependency injection container.

    This container manages services and can be easily extended with new services.
    """

    # Parent container for shared dependencies
    config = providers.Configuration()

    # Template service
    template_service = providers.Factory(
        TemplateService,
    )

    # Future services can be added here:
    # auth_service = providers.Factory(AuthService, ...)
