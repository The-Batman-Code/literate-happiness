"""LinkedIn search agent factory."""

from google.adk.agents import Agent

from src.app.agents.job_search_agent.prompts import (
    get_job_search_description,
    get_job_search_instructions,
)
from src.app.agents.job_search_agent.tools import (
    analyze_salary_trends,
    get_historical_salary_trends,
    get_linkedin_mcp_server,
    get_regional_job_stats,
    get_top_hiring_companies,
    list_job_categories,
    search_adzuna_jobs,
)
from src.app.core import get_settings, logger

# Create root agent at module level for ADK
settings = get_settings()
model = settings.google_model

logger.info("Initializing Job search agent")

linkedin_mcp = get_linkedin_mcp_server()

root_agent = Agent(
    name="job_search_agent",
    model=model,
    description=get_job_search_description(),
    instruction=get_job_search_instructions(),
    tools=[
        # linkedin_mcp,
        search_adzuna_jobs,
        analyze_salary_trends,
        get_top_hiring_companies,
        list_job_categories,
        get_regional_job_stats,
        get_historical_salary_trends,
    ],
)

logger.info("Job search agent created successfully")
