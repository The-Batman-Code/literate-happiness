"""LinkedIn search agent factory."""

from google.adk.agents import Agent

from src.app.agents.linkedin_search_agent.tools import (
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

logger.info("Initializing LinkedIn search agent")

linkedin_mcp = get_linkedin_mcp_server()

root_agent = Agent(
    name="linkedin_search_agent",
    model=model,
    description="LinkedIn job search and candidate research specialist",
    instruction="""You are an expert LinkedIn researcher and job search specialist.

Your responsibilities:
1. Search for job opportunities and market data using Adzuna tools
2. Research candidate profiles and career information via LinkedIn
3. Extract key insights and qualifications from profiles
4. Provide analysis of job market trends, salary distributions, and hiring companies

Always use the appropriate tools to retrieve accurate, current information 
from both LinkedIn and Adzuna.""",
    tools=[
        linkedin_mcp,
        search_adzuna_jobs,
        analyze_salary_trends,
        get_top_hiring_companies,
        list_job_categories,
        get_regional_job_stats,
        get_historical_salary_trends,
    ],
)

logger.info("LinkedIn search agent created successfully")
