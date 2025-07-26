import logging

import dotenv
import requests
from mcp.server.fastmcp import FastMCP

dotenv.load_dotenv()  # Load environment variables from .env file mainly for proxy settings to be able to ping the Weather api

logger = logging.getLogger(__name__)

# Create the MCP server instance with the name "Weather"
mcp = FastMCP("Weather")


@mcp.tool()
def get_current_weather(city: str) -> str:
    """
    Get current weather for a given city.
    For a real implementation, we use an API call to wttr.in.
    If needed, this can be replaced with a dummy function.
    """
    print("IN WEATHER SERVER")
    logger.info(f"Weather tool 'get_current_weather' invoked with city: {city}")
    try:
        # Using wttr.in to get a brief weather report; you can adjust formatting as needed.
        endpoint = f"https://wttr.in/{city}?format=3"
        response = requests.get(endpoint)
        response.raise_for_status()  # Raise exception for non-200 status codes
        result = response.text
        logger.info(f"Weather tool 'get_current_weather' result: {result}")
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"Error retrieving weather data: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        logger.exception("Unexpected error in get_current_weather")
        return f"Error retrieving weather data: {e}"


if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run(transport="stdio")
