"""Adzuna service exceptions."""


class AdzunaServiceException(Exception):
    """Base exception for Adzuna service errors."""


class AdzunaAuthenticationError(AdzunaServiceException):
    """Raised when Adzuna API credentials are missing or invalid."""


class AdzunaAPIError(AdzunaServiceException):
    """Raised when Adzuna API returns an error response."""


__all__ = [
    "AdzunaServiceException",
    "AdzunaAuthenticationError",
    "AdzunaAPIError",
]
