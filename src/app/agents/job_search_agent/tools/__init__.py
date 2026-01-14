"""LinkedIn search agent tools."""

from src.app.agents.job_search_agent.tools.adzuna_tools import (
    analyze_salary_trends,
    get_historical_salary_trends,
    get_regional_job_stats,
    get_top_hiring_companies,
    list_job_categories,
    search_adzuna_jobs,
)
from src.app.agents.job_search_agent.tools.mcp_servers import (
    get_linkedin_mcp_server,
)

__all__ = [
    # MCP servers
    "get_linkedin_mcp_server",
    # Adzuna tools
    "search_adzuna_jobs",
    "analyze_salary_trends",
    "get_top_hiring_companies",
    "list_job_categories",
    "get_regional_job_stats",
    "get_historical_salary_trends",
]
