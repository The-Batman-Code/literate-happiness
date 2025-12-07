"""LinkedIn search agent factory."""

from google.adk.agents import Agent

from src.app.agents.linkedin_search_agent.tools import get_linkedin_mcp_server
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
1. Search for job opportunities based on user criteria (title, location, company)
2. Research candidate profiles and career information
3. Extract key insights and qualifications from profiles
4. Provide analysis of job market trends and opportunities

Always use the LinkedIn tools to retrieve accurate, current information.""",
    tools=[linkedin_mcp],
)

logger.info("LinkedIn search agent created successfully")
