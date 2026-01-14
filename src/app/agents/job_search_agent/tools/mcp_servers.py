from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from src.app.core import get_settings, logger


def get_linkedin_mcp_server() -> McpToolset:
    """
    Connect to LinkedIn MCP server running via Docker or uvx.

    The LinkedIn MCP server must be running externally (in Docker or uvx).
    This function connects to it using stdio protocol.

    Configuration:
    - Reads LinkedIn cookie from LINKEDIN_COOKIE environment variable
    - Accessed via centralized config (src.app.core.config)

    Returns:
        McpToolset: Configured LinkedIn MCP toolset
    """
    settings = get_settings()
    linkedin_cookie = settings.linkedin_cookie or ""

    if not linkedin_cookie:
        logger.warning("LinkedIn cookie not configured in .env")

    # Using uvx (recommended - no local install needed)
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="uvx",
                args=[
                    "--from",
                    "git+https://github.com/stickerdaniel/linkedin-mcp-server",
                    "linkedin-mcp-server",
                ],
                env={"LINKEDIN_COOKIE": linkedin_cookie},
            ),
            timeout=300.0,
        ),
    )
