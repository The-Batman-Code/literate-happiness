"""Adzuna API service for job search and salary data.

Production-grade service layer for Adzuna API v1 integration.
Handles HTTP requests, authentication, error handling, and response parsing.
"""

from typing import Any

import httpx
from pydantic import SecretStr

from src.app.core import get_settings, logger
from src.app.schemas import (
    AdzunaCategoriesParams,
    AdzunaCategoriesResponse,
    AdzunaGeodataParams,
    AdzunaGeodataResponse,
    AdzunaHistogramParams,
    AdzunaHistogramResponse,
    AdzunaHistoricalParams,
    AdzunaHistoricalResponse,
    AdzunaSearchParams,
    AdzunaSearchResponse,
    AdzunaTopCompaniesParams,
    AdzunaTopCompaniesResponse,
)
from src.app.services.adzuna.exceptions import (
    AdzunaAPIError,
    AdzunaAuthenticationError,
    AdzunaServiceException,
)


class AdzunaService:
    """Service for interacting with Adzuna Job API v1.

    Handles all HTTP requests to Adzuna API endpoints with proper
    authentication, error handling, and response parsing.

    Base URL: https://api.adzuna.com/v1/api
    """

    BASE_URL = "https://api.adzuna.com/v1/api"
    TIMEOUT = 30.0  # seconds

    def __init__(
        self,
        app_id: SecretStr | None = None,
        app_key: SecretStr | None = None,
    ) -> None:
        """Initialize Adzuna service.

        Args:
            app_id: Adzuna application ID (optional, defaults to config)
            app_key: Adzuna application key (optional, defaults to config)

        Raises:
            AdzunaAuthenticationError: If credentials are not provided or
                configured
        """
        settings = get_settings()

        self.app_id = app_id or settings.adzuna_app_id
        self.app_key = app_key or settings.adzuna_app_key

        if not self.app_id or not self.app_key:
            msg = (
                "Adzuna API credentials not configured. "
                "Set ADZUNA_APP_ID and ADZUNA_APP_KEY in .env"
            )
            logger.error("Adzuna API credentials not configured")
            raise AdzunaAuthenticationError(msg)

        logger.bind(service="adzuna").info("Adzuna service initialized")

    def _get_auth_params(self) -> dict[str, str]:
        """Get authentication query parameters.

        Returns:
            Dict with app_id and app_key for API authentication

        Raises:
            AdzunaAuthenticationError: If credentials are not set
        """
        if not self.app_id or not self.app_key:
            msg = "Adzuna API credentials not initialized"
            raise AdzunaAuthenticationError(msg)

        return {
            "app_id": self.app_id.get_secret_value(),
            "app_key": self.app_key.get_secret_value(),
        }

    async def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make authenticated HTTP request to Adzuna API.

        Args:
            endpoint: API endpoint path (e.g., "jobs/us/search/1")
            params: Query parameters (auth params are added automatically)

        Returns:
            Parsed JSON response

        Raises:
            AdzunaAuthenticationError: If credentials are invalid
            AdzunaAPIError: If API returns error status code
            AdzunaServiceException: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        all_params = {**(params or {}), **self._get_auth_params()}

        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                response = await client.get(url, params=all_params)
        except httpx.TimeoutException as e:
            logger.exception("Adzuna API request timeout after %ss", self.TIMEOUT)
            raise AdzunaServiceException(
                f"Adzuna API request timeout after {self.TIMEOUT}s",
            ) from e
        except httpx.HTTPError as e:
            logger.exception("Adzuna API HTTP error: %s", e)
            raise AdzunaServiceException(f"Adzuna API HTTP error: {e}") from e
        except Exception as e:
            logger.bind(error_type=type(e).__name__).exception(
                "Unexpected error calling Adzuna API",
            )
            raise AdzunaServiceException(f"Unexpected error calling Adzuna API: {e}") from e

        # Handle API-specific errors outside the httpx try/except block to avoid
        # swallowing custom exceptions into AdzunaServiceException
        if response.status_code == 401:
            logger.error("Invalid Adzuna API credentials")
            raise AdzunaAuthenticationError("Invalid Adzuna API credentials")

        if response.status_code == 429:
            logger.warning("Adzuna API rate limit exceeded")
            raise AdzunaAPIError("Adzuna API rate limit exceeded")

        if response.status_code >= 400:
            logger.bind(
                status_code=response.status_code,
                response_text=response.text,
            ).error("Adzuna API error: %s - %s", response.status_code, response.text)
            raise AdzunaAPIError(f"Adzuna API error: {response.status_code}")

        return response.json()

    # ========================================================================
    # Job Search Endpoint
    # ========================================================================

    async def search_jobs(
        self,
        params: AdzunaSearchParams,
    ) -> AdzunaSearchResponse:
        """Search for job listings.

        Endpoint: GET /jobs/{country}/search/{page}

        Args:
            params: Search parameters (keywords, location, filters)

        Returns:
            Paginated job search results

        Raises:
            AdzunaAPIError: If API request fails
        """
        endpoint = f"jobs/{params.country}/search/{params.page}"

        # Build query params (exclude country/page as they're in URL)
        query_params = params.model_dump(
            exclude={"country", "page"},
            exclude_none=True,
        )

        logger.bind(
            endpoint=endpoint,
            what=params.what,
            where=params.where,
        ).info("Searching Adzuna jobs")

        try:
            data = await self._make_request(endpoint, query_params)
            return AdzunaSearchResponse.model_validate(data)
        except Exception as e:
            logger.bind(
                error_type=type(e).__name__,
                endpoint=endpoint,
            ).exception("Job search failed")
            raise

    # ========================================================================
    # Salary Histogram Endpoint
    # ========================================================================

    async def get_salary_histogram(
        self,
        params: AdzunaHistogramParams,
    ) -> AdzunaHistogramResponse:
        """Get salary distribution histogram.

        Endpoint: GET /jobs/{country}/histogram

        Args:
            params: Histogram query parameters

        Returns:
            Salary distribution buckets

        Raises:
            AdzunaAPIError: If API request fails
        """
        endpoint = f"jobs/{params.country}/histogram"

        query_params = params.model_dump(
            exclude={"country"},
            exclude_none=True,
        )

        logger.bind(endpoint=endpoint).info("Fetching salary histogram")

        try:
            data = await self._make_request(endpoint, query_params)
            return AdzunaHistogramResponse.model_validate(data)
        except Exception as e:
            logger.bind(
                error_type=type(e).__name__,
                endpoint=endpoint,
            ).exception("Histogram fetch failed")
            raise

    # ========================================================================
    # Historical Data Endpoint
    # ========================================================================

    async def get_historical_data(
        self,
        params: AdzunaHistoricalParams,
    ) -> AdzunaHistoricalResponse:
        """Get historical salary and vacancy trends.

        Endpoint: GET /jobs/{country}/history

        Args:
            params: Historical data query parameters

        Returns:
            Historical salary and vacancy data by month

        Raises:
            AdzunaAPIError: If API request fails
        """
        endpoint = f"jobs/{params.country}/history"

        query_params = params.model_dump(
            exclude={"country"},
            exclude_none=True,
        )

        logger.bind(endpoint=endpoint, months=params.months).info(
            "Fetching historical data",
        )

        try:
            data = await self._make_request(endpoint, query_params)
            return AdzunaHistoricalResponse.model_validate(data)
        except Exception as e:
            logger.bind(
                error_type=type(e).__name__,
                endpoint=endpoint,
            ).exception("Historical data fetch failed")
            raise

    # ========================================================================
    # Geodata (Regional) Endpoint
    # ========================================================================

    async def get_geodata(
        self,
        params: AdzunaGeodataParams,
    ) -> AdzunaGeodataResponse:
        """Get job counts by sub-region.

        Endpoint: GET /jobs/{country}/geodata

        Args:
            params: Geodata query parameters

        Returns:
            Job counts by sub-region

        Raises:
            AdzunaAPIError: If API request fails
        """
        endpoint = f"jobs/{params.country}/geodata"

        query_params = params.model_dump(
            exclude={"country"},
            exclude_none=True,
        )

        logger.bind(endpoint=endpoint).info("Fetching geodata")

        try:
            data = await self._make_request(endpoint, query_params)
            return AdzunaGeodataResponse.model_validate(data)
        except Exception as e:
            logger.bind(
                error_type=type(e).__name__,
                endpoint=endpoint,
            ).exception("Geodata fetch failed")
            raise

    # ========================================================================
    # Top Companies Endpoint
    # ========================================================================

    async def get_top_companies(
        self,
        params: AdzunaTopCompaniesParams,
    ) -> AdzunaTopCompaniesResponse:
        """Get top 5 companies by vacancy count.

        Endpoint: GET /jobs/{country}/top_companies

        Args:
            params: Top companies query parameters

        Returns:
            Top 5 companies ranked by number of vacancies

        Raises:
            AdzunaAPIError: If API request fails
        """
        endpoint = f"jobs/{params.country}/top_companies"

        query_params = params.model_dump(
            exclude={"country"},
            exclude_none=True,
        )

        logger.bind(endpoint=endpoint).info("Fetching top companies")

        try:
            data = await self._make_request(endpoint, query_params)
            return AdzunaTopCompaniesResponse.model_validate(data)
        except Exception as e:
            logger.bind(
                error_type=type(e).__name__,
                endpoint=endpoint,
            ).exception("Top companies fetch failed")
            raise

    # ========================================================================
    # Categories Endpoint
    # ========================================================================

    async def get_categories(
        self,
        params: AdzunaCategoriesParams,
    ) -> AdzunaCategoriesResponse:
        """Get all available job categories.

        Endpoint: GET /jobs/{country}/categories

        Args:
            params: Categories query parameters

        Returns:
            List of all job categories

        Raises:
            AdzunaAPIError: If API request fails
        """
        endpoint = f"jobs/{params.country}/categories"

        query_params = params.model_dump(
            exclude={"country"},
            exclude_none=True,
        )

        logger.bind(endpoint=endpoint).info("Fetching categories")

        try:
            data = await self._make_request(endpoint, query_params)
            return AdzunaCategoriesResponse.model_validate(data)
        except Exception as e:
            logger.bind(
                error_type=type(e).__name__,
                endpoint=endpoint,
            ).exception("Categories fetch failed")
            raise


__all__ = [
    "AdzunaService",
]
