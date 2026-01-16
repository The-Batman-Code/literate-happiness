"""LinkedIn search agent factory."""

from google.adk.agents import Agent
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps import App

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

# Option 1: Wrap agent in App with Context Cache Config for UI testing
# Setting min_tokens to 100 for easier verification with shorter instructions
app = App(
    name="job_search_agent",
    root_agent=root_agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=100,
        ttl_seconds=600,
    ),
)

logger.info("Job search agent and App with Caching created successfully")
