"""Pydantic input schemas for LinkedIn search agent tools.

These schemas define the inputs for agent tools, providing type validation
and descriptions for the LLM to understand tool parameters.
"""

from pydantic import BaseModel, Field


class JobSearchInput(BaseModel):
    """Input schema for job search tool."""

    query: str = Field(
        description="Keywords to search for (e.g., 'Python developer', 'Data scientist')",
    )
    location: str | None = Field(
        default=None,
        description="Location to search in (e.g., 'San Francisco', 'Remote')",
    )
    country: str = Field(
        default="us",
        description="Country code (us, uk, de, etc.)",
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of results to return (1-50)",
    )


class SalaryAnalysisInput(BaseModel):
    """Input schema for salary analysis tool."""

    job_title: str = Field(
        description="Job title to analyze (e.g., 'Software Engineer', 'Product Manager')",
    )
    location: str | None = Field(
        default=None,
        description="Location to analyze (optional)",
    )
    country: str = Field(
        default="us",
        description="Country code (us, uk, de, etc.)",
    )


class TopCompaniesInput(BaseModel):
    """Input schema for top hiring companies tool."""

    job_category: str | None = Field(
        default=None,
        description="Job category (e.g., 'IT Jobs', 'Engineering Jobs')",
    )
    location: str | None = Field(
        default=None,
        description="Location to search (optional)",
    )
    country: str = Field(
        default="us",
        description="Country code (us, uk, de, etc.)",
    )


__all__ = [
    "JobSearchInput",
    "SalaryAnalysisInput",
    "TopCompaniesInput",
]
