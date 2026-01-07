"""LinkedIn search agent schemas."""

from src.app.agents.linkedin_search_agent.schemas.tool_inputs import (
    HistoricalTrendsInput,
    JobCategoriesInput,
    JobSearchInput,
    RegionalStatsInput,
    SalaryAnalysisInput,
    TopCompaniesInput,
)

__all__ = [
    "JobSearchInput",
    "SalaryAnalysisInput",
    "TopCompaniesInput",
    "HistoricalTrendsInput",
    "JobCategoriesInput",
    "RegionalStatsInput",
]
