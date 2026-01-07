"""Application-level dependency injection container.

Uses modern-di for managing service lifecycles and dependencies.
"""

from collections.abc import Iterator

from modern_di import Group, Scope, providers

from src.app.services.adzuna.service import AdzunaService


def create_adzuna_service() -> Iterator[AdzunaService]:
    """Factory function to create Adzuna service instance.

    Credentials are loaded from settings within the service __init__.

    Yields:
        Initialized AdzunaService instance
    """
    yield AdzunaService()


class AppDependencies(Group):
    """Main application dependency injection container.

    Defines all application-level services and their scopes.
    Uses modern-di for automatic dependency resolution.
    """

    # Adzuna service - APP scope (singleton for entire application)
    adzuna_service: providers.Resource[AdzunaService] = providers.Resource(
        Scope.APP,
        create_adzuna_service,
    )


__all__ = ["AppDependencies", "create_adzuna_service"]
