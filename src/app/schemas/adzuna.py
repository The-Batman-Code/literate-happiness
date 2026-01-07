"""Pydantic models for Adzuna API integration.

All schemas model the Adzuna API v1 request/response structure.
See: https://api.adzuna.com/v1/doc
"""

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Shared/Common Models
# ============================================================================


class AdzunaCompany(BaseModel):
    """Company information from Adzuna API."""

    display_name: str = Field(..., description="Company display name")


class AdzunaLocation(BaseModel):
    """Location information from Adzuna API."""

    display_name: str | None = Field(default=None, description="Human-readable location name")
    area: list[str] = Field(
        default_factory=list,
        description="Location hierarchy (e.g., ['UK', 'London', 'Central London'])",
    )


class AdzunaCategory(BaseModel):
    """Job category from Adzuna API."""

    tag: str = Field(..., description="Category tag/identifier")
    label: str = Field(..., description="Human-readable category label")


# ============================================================================
# Job Search Endpoint
# ============================================================================


class AdzunaSearchParams(BaseModel):
    """Query parameters for job search endpoint.

    Endpoint: GET /v1/api/jobs/{country}/search/{page}
    """

    # Required
    country: str = Field(
        default="us",
        description="Two-letter country code (e.g., 'us', 'gb', 'ca')",
    )
    page: int = Field(default=1, ge=1, description="Page number for pagination")

    # Search filters
    what: str | None = Field(
        default=None,
        description="Keywords to search in job title/description (e.g., 'python developer')",
    )
    where: str | None = Field(
        default=None,
        description="Location to search (e.g., 'New York', 'London')",
    )

    # Salary filters
    salary_min: int | None = Field(
        default=None,
        ge=0,
        description="Minimum salary (annual)",
    )
    salary_max: int | None = Field(
        default=None,
        ge=0,
        description="Maximum salary (annual)",
    )

    # Contract filters
    full_time: bool | None = Field(
        default=None,
        description="Filter for full-time positions only",
    )
    part_time: bool | None = Field(
        default=None,
        description="Filter for part-time positions only",
    )
    permanent: bool | None = Field(
        default=None,
        description="Filter for permanent positions only",
    )
    contract: bool | None = Field(
        default=None,
        description="Filter for contract positions only",
    )

    # Pagination
    results_per_page: int = Field(
        default=20,
        ge=1,
        le=50,
        description="Number of results per page (max 50)",
    )

    # Other filters
    category: str | None = Field(
        default=None,
        description="Job category tag (use categories endpoint to get valid tags)",
    )
    sort_by: str | None = Field(
        default="relevance",
        description="Sort order: 'relevance', 'date', 'salary'",
    )

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Ensure country code is lowercase."""
        return v.lower().strip()


class AdzunaJobListing(BaseModel):
    """Single job listing from Adzuna search results."""

    id: str = Field(..., description="Unique job ID")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Full job description (HTML/text)")
    created: str = Field(..., description="Job posting creation date (ISO 8601)")

    company: AdzunaCompany = Field(..., description="Company information")
    location: AdzunaLocation = Field(..., description="Job location")

    redirect_url: str = Field(
        ...,
        description="URL to view full job posting on source site",
    )

    # Optional fields
    salary_min: float | None = Field(
        default=None,
        description="Minimum salary (if available)",
    )
    salary_max: float | None = Field(
        default=None,
        description="Maximum salary (if available)",
    )
    salary_is_predicted: bool | None = Field(
        default=None,
        description="Whether salary is predicted by Adzuna",
    )
    contract_type: str | None = Field(
        default=None,
        description="Contract type (e.g., 'permanent', 'contract')",
    )
    contract_time: str | None = Field(
        default=None,
        description="Full-time/part-time indicator",
    )
    category: AdzunaCategory | None = Field(
        default=None,
        description="Job category",
    )


class AdzunaSearchResponse(BaseModel):
    """Response from job search endpoint."""

    results: list[AdzunaJobListing] = Field(
        default_factory=list,
        description="List of job listings",
    )
    count: int = Field(..., description="Total number of results available")
    mean: float | None = Field(
        default=None,
        description="Mean salary for search results",
    )


# ============================================================================
# Salary Histogram Endpoint
# ============================================================================


class AdzunaHistogramParams(BaseModel):
    """Query parameters for salary histogram endpoint.

    Endpoint: GET /v1/api/jobs/{country}/histogram
    """

    country: str = Field(
        default="us",
        description="Two-letter country code",
    )
    what: str | None = Field(
        default=None,
        description="Job title/keywords to filter",
    )
    where: str | None = Field(
        default=None,
        description="Location to filter",
    )


class AdzunaHistogramBucket(BaseModel):
    """Single bucket in salary histogram."""

    label: int = Field(..., description="Lower bound of salary range for this bucket")
    count: int = Field(..., description="Number of jobs in this salary range")


class AdzunaHistogramResponse(BaseModel):
    """Response from histogram endpoint."""

    histogram: dict[str, int] = Field(
        default_factory=dict,
        description="Salary distribution buckets (salary_min as key, count as value)",
    )


# ============================================================================
# Historical Data Endpoint
# ============================================================================


class AdzunaHistoricalParams(BaseModel):
    """Query parameters for historical salary/vacancy data endpoint.

    Endpoint: GET /v1/api/jobs/{country}/history
    """

    country: str = Field(default="us", description="Two-letter country code")
    what: str | None = Field(default=None, description="Job title/keywords")
    where: str | None = Field(default=None, description="Location")
    months: int = Field(
        default=12,
        ge=1,
        le=24,
        description="Number of months of historical data (max 24)",
    )


class AdzunaHistoricalDataPoint(BaseModel):
    """Single data point in historical data."""

    month: str = Field(..., description="Month (YYYY-MM format)")
    average_salary: float | None = Field(
        default=None,
        description="Average salary for that month",
    )
    vacancy_count: int = Field(..., description="Number of vacancies")


class AdzunaHistoricalResponse(BaseModel):
    """Response from historical data endpoint."""

    month: dict[str, float] = Field(
        default_factory=dict,
        description="Historical average salary data (YYYY-MM as key, salary as value)",
    )


# ============================================================================
# Geodata (Regional) Endpoint
# ============================================================================


class AdzunaGeodataParams(BaseModel):
    """Query parameters for regional geodata endpoint.

    Endpoint: GET /v1/api/jobs/{country}/geodata
    """

    country: str = Field(default="us", description="Two-letter country code")
    where: str | None = Field(
        default=None,
        description="Parent location to get sub-regions for",
    )
    category: str | None = Field(
        default=None,
        description="Filter by job category",
    )


class AdzunaGeodataLocation(BaseModel):
    """Regional job count data."""

    location: AdzunaLocation = Field(..., description="Sub-region location")
    count: int = Field(..., description="Number of jobs in this sub-region")


class AdzunaGeodataResponse(BaseModel):
    """Response from geodata endpoint."""

    locations: list[AdzunaGeodataLocation] = Field(
        default_factory=list,
        description="Job counts by sub-region",
    )


# ============================================================================
# Top Companies Endpoint
# ============================================================================


class AdzunaTopCompaniesParams(BaseModel):
    """Query parameters for top companies endpoint.

    Endpoint: GET /v1/api/jobs/{country}/top_companies
    """

    country: str = Field(default="us", description="Two-letter country code")
    what: str | None = Field(default=None, description="Job title/keywords filter")
    where: str | None = Field(default=None, description="Location filter")


class AdzunaTopCompany(BaseModel):
    """Company with vacancy count."""

    name: str = Field(..., description="Company name")
    count: int = Field(..., description="Number of current vacancies")


class AdzunaTopCompaniesResponse(BaseModel):
    """Response from top companies endpoint (returns top 5)."""

    leaderboard: list[AdzunaTopCompany] = Field(
        default_factory=list,
        description="Top 5 companies by vacancy count",
    )


# ============================================================================
# Categories Endpoint
# ============================================================================


class AdzunaCategoriesParams(BaseModel):
    """Query parameters for categories endpoint.

    Endpoint: GET /v1/api/jobs/{country}/categories
    """

    country: str = Field(default="us", description="Two-letter country code")


class AdzunaCategoriesResponse(BaseModel):
    """Response from categories endpoint."""

    results: list[AdzunaCategory] = Field(
        default_factory=list,
        description="List of all available job categories",
    )


__all__ = [
    # Shared models
    "AdzunaCompany",
    "AdzunaLocation",
    "AdzunaCategory",
    # Search
    "AdzunaSearchParams",
    "AdzunaJobListing",
    "AdzunaSearchResponse",
    # Histogram
    "AdzunaHistogramParams",
    "AdzunaHistogramBucket",
    "AdzunaHistogramResponse",
    # Historical
    "AdzunaHistoricalParams",
    "AdzunaHistoricalDataPoint",
    "AdzunaHistoricalResponse",
    # Geodata
    "AdzunaGeodataParams",
    "AdzunaGeodataLocation",
    "AdzunaGeodataResponse",
    # Top Companies
    "AdzunaTopCompaniesParams",
    "AdzunaTopCompany",
    "AdzunaTopCompaniesResponse",
    # Categories
    "AdzunaCategoriesParams",
    "AdzunaCategoriesResponse",
]
