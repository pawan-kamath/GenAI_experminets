import json
import logging
import os
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "weather"
LOCATION_CACHE_FILE = CACHE_DIR / "location_cache.json"


class WeatherTools(str, Enum):
    """Enumeration of all weather tools available in the server."""

    GET_CURRENT_WEATHER = "get_current_weather"
    GET_FORECAST = "get_forecast"


class WeatherServer:
    """
    A server that provides weather information using the AccuWeather API.
    """

    def __init__(self, name: str = "Weather"):
        self.name = name
        self.mcp = FastMCP(name)
        self.api_key = os.getenv("ACCUWEATHER_API_KEY")
        self.base_url = "http://dataservice.accuweather.com"

        # Set up proxy from environment variables
        self.proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
        self.no_proxy = os.getenv("NO_PROXY", "")

        logger.info(f"Initializing Weather server with proxy: {self.proxy}")
        logger.info(f"NO_PROXY settings: {self.no_proxy}")
        logger.info(f"AccuWeather API key available: {'Yes' if self.api_key else 'No'}")

        self.setup_tools()

    def setup_tools(self):
        """Register all tools with the MCP server."""
        self.mcp.tool()(self.get_current_weather)
        self.mcp.tool()(self.get_forecast)

    def get_cached_location_key(self, location: str) -> Optional[str]:
        """
        Get location key from cache.

        Args:
            location: The location to get the key for.

        Returns:
            The location key if found in cache, None otherwise.
        """
        if not LOCATION_CACHE_FILE.exists():
            return None

        try:
            with open(LOCATION_CACHE_FILE) as f:
                cache = json.load(f)
                return cache.get(location)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def cache_location_key(self, location: str, location_key: str):
        """
        Cache location key for future use.

        Args:
            location: The location to cache the key for.
            location_key: The location key to cache.
        """
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        try:
            if LOCATION_CACHE_FILE.exists():
                with open(LOCATION_CACHE_FILE) as f:
                    cache = json.load(f)
            else:
                cache = {}

            cache[location] = location_key

            with open(LOCATION_CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache location key: {e}")

    def _should_use_proxy(self, url: str) -> bool:
        """
        Determine if a proxy should be used for a given URL based on NO_PROXY env var.

        Args:
            url: The URL to check.

        Returns:
            True if proxy should be used, False otherwise.
        """
        if not self.proxy or not url:
            return False

        # Parse the hostname from the URL
        from urllib.parse import urlparse

        hostname = urlparse(url).netloc

        # Check against NO_PROXY patterns
        if self.no_proxy:
            no_proxy_list = self.no_proxy.replace(" ", "").split(",")
            for pattern in no_proxy_list:
                if pattern in hostname or hostname.endswith(f".{pattern.lstrip('.')}"):
                    return False

        return True

    async def _create_client_session(self) -> ClientSession:
        """
        Create an aiohttp client session with appropriate proxy settings.

        Returns:
            Configured aiohttp ClientSession object.
        """
        proxy_url = None
        if self._should_use_proxy(self.base_url):
            proxy_url = self.proxy
            logger.info(f"Using proxy {proxy_url} for AccuWeather API")
        else:
            logger.info(
                "No proxy will be used for AccuWeather API (matches NO_PROXY rules)"
            )

        # Set up TCP connector with reasonable timeouts
        connector = TCPConnector(ssl=False, limit=10)

        # Set up more generous timeouts for corporate environment
        timeout = ClientTimeout(total=30, connect=10, sock_connect=10, sock_read=10)

        return ClientSession(
            connector=connector,
            timeout=timeout,
            proxy=proxy_url,
            trust_env=True,  # Trust environment variables for proxy settings
        )

    async def get_location_key(
        self, location: str, session: ClientSession
    ) -> tuple[str, dict[str, Any]]:
        """
        Get the location key for a location using the AccuWeather API.

        Args:
            location: The location to get the key for.
            session: The aiohttp session to use for the request.

        Returns:
            A tuple containing the location key and full location data.

        Raises:
            Exception: If the location cannot be found or the API request fails.
        """
        # Try to get location key from cache first
        cached_key = self.get_cached_location_key(location)
        if cached_key:
            logger.info(f"Using cached location key for {location}: {cached_key}")
            # Since we only have the key in cache but not the full location data,
            # we'll still need to make an API call to get the location details
            # so we'll proceed with the API call as if no cache was found

        # If not in cache or we need full location data, request from API
        location_search_url = f"{self.base_url}/locations/v1/cities/search"
        params = {
            "apikey": self.api_key,
            "q": location,
        }

        logger.info(
            f"Sending request to AccuWeather API: {location_search_url} with params: {params}"
        )

        try:
            async with session.get(location_search_url, params=params) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_message = (
                        f"Error fetching location data: {response.status}, {error_text}"
                    )
                    logger.error(error_message)
                    raise Exception(error_message)

                locations = await response.json()

                if not locations or len(locations) == 0:
                    error_message = f"Location not found: {location}"
                    logger.error(error_message)
                    raise Exception(error_message)

                # Default to the first result
                selected_location = locations[0]

                # Log all found locations for debugging
                logger.info(f"Found {len(locations)} locations for query '{location}':")
                for i, loc in enumerate(
                    locations[:5]
                ):  # Log first 5 only to avoid excessive logging
                    country = loc.get("Country", {}).get("EnglishName", "Unknown")
                    name = loc.get("LocalizedName", "Unknown")
                    key = loc.get("Key", "Unknown")
                    logger.info(f"  {i + 1}. {name}, {country} (Key: {key})")

                # Check if a more specific location matching is required
                # For example, if looking for "Dingle, Ireland" specifically
                if "," in location:
                    parts = location.split(",")
                    city_name = parts[0].strip()
                    country_name = parts[1].strip()

                    # Try to find a match for both city and country
                    for loc in locations:
                        country = loc.get("Country", {}).get("EnglishName", "")
                        if (
                            loc.get("LocalizedName") == city_name
                            and country_name.lower() in country.lower()
                        ):
                            selected_location = loc
                            logger.info(
                                f"Selected location based on city and country match: {city_name}, {country}"
                            )
                            break

                # If looking for a specific country, try to match it
                elif len(locations) > 1:
                    # Example: filter by country for places like "Dingle" (which exists in multiple countries)
                    # Prefer Ireland if it's in the list for the Dingle example
                    ireland_location = None
                    for loc in locations:
                        country = loc.get("Country", {}).get("EnglishName", "")
                        if country == "Ireland":
                            ireland_location = loc
                            logger.info(
                                f"Found Ireland location: {loc.get('LocalizedName')}, {country}"
                            )
                            break

                    if ireland_location:
                        selected_location = ireland_location
                        logger.info(
                            f"Selected Ireland location over default: {ireland_location.get('LocalizedName')}, Ireland"
                        )

                location_key = selected_location["Key"]
                logger.info(
                    f"Final selected location: {selected_location.get('LocalizedName')}, {selected_location.get('Country', {}).get('EnglishName', 'Unknown')} with key: {location_key}"
                )

                # Cache the location key for future use
                self.cache_location_key(location, location_key)

                return location_key, selected_location
        except aiohttp.ClientError as e:
            logger.exception(f"Network error in get_location_key: {str(e)}")
            raise Exception(
                f"Network error when connecting to AccuWeather API: {str(e)}"
            )
        except Exception as e:
            logger.exception(f"Error in get_location_key: {str(e)}")
            raise

    async def get_current_weather(self, location: str) -> str:
        """
        Get the current weather for a location.

        Args:
            location: The location to get weather for.

        Returns:
            A formatted string with current weather information.
        """
        logger.info(
            f"Weather tool 'get_current_weather' invoked with location: {location}"
        )

        try:
            if not self.api_key:
                raise Exception(
                    "AccuWeather API key not found. Please set the ACCUWEATHER_API_KEY environment variable."
                )

            async with await self._create_client_session() as session:
                # Get location key
                location_key, location_data = await self.get_location_key(
                    location, session
                )

                # Get current conditions
                current_conditions_url = (
                    f"{self.base_url}/currentconditions/v1/{location_key}"
                )
                params = {"apikey": self.api_key, "details": "true"}

                logger.info(
                    f"Requesting current conditions from: {current_conditions_url}"
                )

                async with session.get(
                    current_conditions_url, params=params
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_message = f"Error fetching current weather data: {response.status}, {error_text}"
                        logger.error(error_message)
                        raise Exception(error_message)

                    current_conditions = await response.json()

                    if not current_conditions or len(current_conditions) == 0:
                        return f"No current weather data available for {location}"

                # Format response
                current = current_conditions[0]
                location_name = location_data["LocalizedName"]
                country = location_data["Country"]["LocalizedName"]
                admin_area = location_data["AdministrativeArea"]["LocalizedName"]

                weather_text = current["WeatherText"]
                temp_c = current["Temperature"]["Metric"]["Value"]
                temp_f = current["Temperature"]["Imperial"]["Value"]
                feels_like_c = current["RealFeelTemperature"]["Metric"]["Value"]
                feels_like_f = current["RealFeelTemperature"]["Imperial"]["Value"]

                humidity = current.get("RelativeHumidity", "N/A")
                pressure_mb = (
                    current.get("Pressure", {}).get("Metric", {}).get("Value", "N/A")
                )
                wind_speed_kph = (
                    current.get("Wind", {})
                    .get("Speed", {})
                    .get("Metric", {})
                    .get("Value", "N/A")
                )
                wind_direction = (
                    current.get("Wind", {}).get("Direction", {}).get("Localized", "N/A")
                )

                uv_index = current.get("UVIndex", "N/A")
                uv_text = current.get("UVIndexText", "N/A")

                cloud_cover = current.get("CloudCover", "N/A")
                visibility_km = (
                    current.get("Visibility", {}).get("Metric", {}).get("Value", "N/A")
                )

                precipitation = (
                    "Yes" if current.get("HasPrecipitation", False) else "No"
                )
                precip_type = current.get("PrecipitationType", "None")

                observation_time = current["LocalObservationDateTime"]

                result = f"""# Current Weather for {location_name}, {admin_area}, {country}

## Current Conditions
- Weather: {weather_text}
- Temperature: {temp_c}°C ({temp_f}°F)
- Feels Like: {feels_like_c}°C ({feels_like_f}°F)
- Humidity: {humidity}%
- Wind: {wind_speed_kph} km/h, {wind_direction}
- Pressure: {pressure_mb} mb
- UV Index: {uv_index} ({uv_text})
- Cloud Cover: {cloud_cover}%
- Visibility: {visibility_km} km
- Precipitation: {precipitation}"""

                if precipitation == "Yes" and precip_type != "None":
                    result += f" ({precip_type})"

                result += f"\n\nLast Updated: {observation_time}"

                logger.info(
                    f"Weather tool 'get_current_weather' executed successfully for {location}"
                )
                return result

        except Exception as e:
            logger.exception(f"Error getting current weather for {location}")
            return f"Error getting current weather for {location}: {str(e)}"

    async def get_forecast(self, location: str, days: int = 5) -> str:
        """
        Get the weather forecast for a location.

        Args:
            location: The location to get the forecast for.
            days: The number of days to forecast (5 or 10).

        Returns:
            A formatted string with forecast information.
        """
        logger.info(
            f"Weather tool 'get_forecast' invoked with location: {location}, days: {days}"
        )

        try:
            if not self.api_key:
                raise Exception(
                    "AccuWeather API key not found. Please set the ACCUWEATHER_API_KEY environment variable."
                )

            # Validate days parameter
            if days not in [5, 10]:
                days = 5  # Default to 5 days if invalid
                logger.warning(
                    f"Invalid days parameter: {days}. Using default value of 5."
                )

            async with await self._create_client_session() as session:
                # Get location key
                location_key, location_data = await self.get_location_key(
                    location, session
                )

                # Get forecast
                forecast_url = (
                    f"{self.base_url}/forecasts/v1/daily/{days}day/{location_key}"
                )
                params = {"apikey": self.api_key, "metric": "true", "details": "true"}

                logger.info(f"Requesting forecast from: {forecast_url}")

                async with session.get(forecast_url, params=params) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_message = f"Error fetching forecast data: {response.status}, {error_text}"
                        logger.error(error_message)
                        raise Exception(error_message)

                    forecast_data = await response.json()

                # Format response
                location_name = location_data["LocalizedName"]
                country = location_data["Country"]["LocalizedName"]
                admin_area = location_data["AdministrativeArea"]["LocalizedName"]

                headline = forecast_data.get("Headline", {}).get(
                    "Text", "No headline available"
                )
                daily_forecasts = forecast_data.get("DailyForecasts", [])

                if not daily_forecasts:
                    return f"No forecast data available for {location}"

                result = f"""# {days}-Day Weather Forecast for {location_name}, {admin_area}, {country}

## Summary
{headline}

## Daily Forecast
"""

                for day in daily_forecasts:
                    date = day["Date"]
                    day_of_week = day.get("Day", {}).get("IconPhrase", "N/A")
                    night = day.get("Night", {}).get("IconPhrase", "N/A")

                    min_temp = day["Temperature"]["Minimum"]["Value"]
                    max_temp = day["Temperature"]["Maximum"]["Value"]

                    rain_prob_day = day.get("Day", {}).get("RainProbability", "N/A")
                    rain_prob_night = day.get("Night", {}).get("RainProbability", "N/A")

                    wind_day = (
                        day.get("Day", {})
                        .get("Wind", {})
                        .get("Speed", {})
                        .get("Value", "N/A")
                    )
                    wind_direction_day = (
                        day.get("Day", {})
                        .get("Wind", {})
                        .get("Direction", {})
                        .get("Localized", "N/A")
                    )

                    result += f"""### {date[:10]}
- Day: {day_of_week}
- Night: {night}
- Temperature: {min_temp}°C - {max_temp}°C
- Rain Probability: {rain_prob_day}% (day), {rain_prob_night}% (night)
- Wind: {wind_day} km/h, {wind_direction_day}

"""

                logger.info(
                    f"Weather tool 'get_forecast' executed successfully for {location}"
                )
                return result

        except Exception as e:
            logger.exception(f"Error getting forecast for {location}")
            return f"Error getting forecast for {location}: {str(e)}"

    def run(self, transport: str = "stdio"):
        """Run the server with the specified transport."""
        self.mcp.run(transport=transport)


async def serve():
    """
    Initialize and run the weather server.
    """
    server = Server("weather-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available weather tools."""
        return [
            Tool(
                name=WeatherTools.GET_CURRENT_WEATHER.value,
                description="Get the current weather for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get weather for (e.g., 'London', 'New York', 'Paris')",
                        }
                    },
                    "required": ["location"],
                },
            ),
            Tool(
                name=WeatherTools.GET_FORECAST.value,
                description="Get the weather forecast for a location",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The location to get the forecast for (e.g., 'London', 'New York', 'Paris')",
                        },
                        "days": {
                            "type": "integer",
                            "description": "The number of days to forecast (5 or 10)",
                            "enum": [5, 10],
                            "default": 5,
                        },
                    },
                    "required": ["location"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls for weather queries."""
        try:
            weather_server = WeatherServer()
            result = ""

            if name == WeatherTools.GET_CURRENT_WEATHER.value:
                if "location" not in arguments:
                    raise ValueError("Missing required argument: location")

                location = arguments["location"]
                result = await weather_server.get_current_weather(location)

            elif name == WeatherTools.GET_FORECAST.value:
                if "location" not in arguments:
                    raise ValueError("Missing required argument: location")

                location = arguments["location"]
                days = arguments.get("days", 5)
                result = await weather_server.get_forecast(location, days)

            else:
                raise ValueError(f"Unknown tool: {name}")

            return [TextContent(type="text", text=result)]
        except Exception as e:
            logger.exception(f"Error processing weather tool call: {str(e)}")
            raise McpError(f"Error processing weather tool call: {str(e)}")

    # Run the server with stdio transport
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    import asyncio

    # For Python 3.7+
    try:
        asyncio.run(serve())
    except AttributeError:
        # Fallback for earlier Python versions
        loop = asyncio.get_event_loop()
        loop.run_until_complete(serve())
