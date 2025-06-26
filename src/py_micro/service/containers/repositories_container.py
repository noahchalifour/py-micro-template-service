from dependency_injector import containers, providers
from modelrepo.factory import get_repository

from py_micro.service.models import HealthCheck


class RepositoriesContainer(containers.DeclarativeContainer):
    """
    Repositories dependency injection container.

    This container manages repositories for model management.
    """

    config = providers.Configuration()

    # Repository factory for creating model repositories
    repository_factory = providers.Factory(
        get_repository,
        class_path=config.class_path,
        kwargs=config.args,
    )

    health_check = providers.Singleton(repository_factory, HealthCheck)
