"""
Dependency injection container for the py_micro.service.

This module sets up the dependency injection container using dependency-injector,
providing centralized configuration and management of all application dependencies.
"""

from .application_container import ApplicationContainer
from .services_container import ServicesContainer
from .repositories_container import RepositoriesContainer

__all__ = ["ApplicationContainer", "ServicesContainer", "RepositoriesContainer"]
