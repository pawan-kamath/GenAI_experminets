# google_search_server.py
import logging

import dotenv
from langchain_google_community import GoogleSearchAPIWrapper
from mcp.server.fastmcp import FastMCP

# Load environment variables.
dotenv.load_dotenv()

logger = logging.getLogger(__name__)

# Create the MCP server instance named "GoogleSearch"
mcp = FastMCP("GoogleSearch")


@mcp.tool()
def google_search(query: str) -> str:
    """
    Use the GoogleSearchAPIWrapper to perform a Google search.
    Ensure that the environment variables GOOGLE_API_KEY and GOOGLE_CSE_ID are set.
    """
    try:
        search = GoogleSearchAPIWrapper()  # Uses the env vars automatically
        logger.info(f"GoogleSearch tool invoked with query: {query}")
        result = search.run(query)
        logger.info(f"GoogleSearch tool result: {result}")
        if not result:
            return "No results found."
        return result
    except Exception as e:
        logger.exception("Error executing Google search")
        return f"Error executing Google search: {str(e)}"


if __name__ == "__main__":
    # Run with stdio transport.
    mcp.run(transport="stdio")
