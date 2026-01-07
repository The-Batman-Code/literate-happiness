"""Adzuna job search API service package.

This package provides a production-grade interface to the Adzuna Job API v1.
All Adzuna-related functionality is contained within this package for modularity.

Service instances are managed by modern-di dependency injection container.
Import from src.app.containers for DI-managed instances.

Exports:
    - AdzunaService: Main service class for API interactions
    - Exceptions: All Adzuna-specific exceptions
"""

from src.app.services.adzuna.exceptions import (
    AdzunaAPIError,
    AdzunaAuthenticationError,
    AdzunaServiceException,
)
from src.app.services.adzuna.service import AdzunaService

__all__ = [
    # Service
    "AdzunaService",
    # Exceptions
    "AdzunaServiceException",
    "AdzunaAuthenticationError",
    "AdzunaAPIError",
]
