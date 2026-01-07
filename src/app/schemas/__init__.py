"""Pydantic schemas for API request/response validation."""

from src.app.schemas.adzuna import (
    AdzunaCategoriesParams,
    AdzunaCategoriesResponse,
    AdzunaCategory,
    AdzunaCompany,
    AdzunaGeodataLocation,
    AdzunaGeodataParams,
    AdzunaGeodataResponse,
    AdzunaHistogramBucket,
    AdzunaHistogramParams,
    AdzunaHistogramResponse,
    AdzunaHistoricalDataPoint,
    AdzunaHistoricalParams,
    AdzunaHistoricalResponse,
    AdzunaJobListing,
    AdzunaLocation,
    AdzunaSearchParams,
    AdzunaSearchResponse,
    AdzunaTopCompaniesParams,
    AdzunaTopCompaniesResponse,
    AdzunaTopCompany,
)

__all__ = [
    # Adzuna - Shared models
    "AdzunaCompany",
    "AdzunaLocation",
    "AdzunaCategory",
    # Adzuna - Search
    "AdzunaSearchParams",
    "AdzunaJobListing",
    "AdzunaSearchResponse",
    # Adzuna - Histogram
    "AdzunaHistogramParams",
    "AdzunaHistogramBucket",
    "AdzunaHistogramResponse",
    # Adzuna - Historical
    "AdzunaHistoricalParams",
    "AdzunaHistoricalDataPoint",
    "AdzunaHistoricalResponse",
    # Adzuna - Geodata
    "AdzunaGeodataParams",
    "AdzunaGeodataLocation",
    "AdzunaGeodataResponse",
    # Adzuna - Top Companies
    "AdzunaTopCompaniesParams",
    "AdzunaTopCompany",
    "AdzunaTopCompaniesResponse",
    # Adzuna - Categories
    "AdzunaCategoriesParams",
    "AdzunaCategoriesResponse",
]
