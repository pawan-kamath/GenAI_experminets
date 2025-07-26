import datetime
import logging
from collections.abc import Sequence
from enum import Enum
from typing import Any, Optional

from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

logger = logging.getLogger(__name__)


class DateTimeTools(str, Enum):
    """Enumeration of all datetime tools available in the server."""

    GET_CURRENT_DATE = "get_current_date"
    GET_CURRENT_TIME = "get_current_time"
    GET_CURRENT_DATETIME = "get_current_datetime"
    GET_DAY_OF_WEEK = "get_day_of_week"
    IS_WEEKEND = "is_weekend"
    GET_DATE_INFO = "get_date_info"
    CONVERT_TIMEZONE = "convert_timezone"


class DateTimeServer:
    """
    A server that provides various date and time functionality.
    """

    def __init__(self, name: str = "DateTime"):
        self.name = name
        self.mcp = FastMCP(name)
        self.setup_tools()

    def setup_tools(self):
        """Register all tools with the MCP server."""
        self.mcp.tool()(self.get_current_date)
        self.mcp.tool()(self.get_current_time)
        self.mcp.tool()(self.get_current_datetime)
        self.mcp.tool()(self.get_day_of_week)
        self.mcp.tool()(self.is_weekend)
        self.mcp.tool()(self.get_date_info)
        self.mcp.tool()(self.convert_timezone)

    def get_current_date(self) -> str:
        """
        Get the current date in YYYY-MM-DD format.
        """
        try:
            result = datetime.datetime.now().strftime("%Y-%m-%d")
            logger.info("Datetime tool 'get_current_date' invoked")
            logger.debug(f"Datetime tool result: {result}")
            return result
        except Exception as e:
            logger.exception("Error getting current date")
            return f"Error getting current date: {str(e)}"

    def get_current_time(self) -> str:
        """
        Get the current time in HH:MM:SS format.
        """
        try:
            result = datetime.datetime.now().strftime("%H:%M:%S")
            logger.info("Datetime tool 'get_current_time' invoked")
            logger.debug(f"Datetime tool result: {result}")
            return result
        except Exception as e:
            logger.exception("Error getting current time")
            return f"Error getting current time: {str(e)}"

    def get_current_datetime(self) -> str:
        """
        Get the current date and time in ISO format.
        """
        try:
            result = datetime.datetime.now().isoformat()
            logger.info("Datetime tool 'get_current_datetime' invoked")
            logger.debug(f"Datetime tool result: {result}")
            return result
        except Exception as e:
            logger.exception("Error getting current datetime")
            return f"Error getting current datetime: {str(e)}"

    def get_day_of_week(self, date: Optional[str] = None) -> str:
        """
        Get the day of week for a given date or today.

        Args:
            date: Optional date in YYYY-MM-DD format. Defaults to today.

        Returns:
            Day of week (Monday, Tuesday, etc.)
        """
        logger.info(
            f"Datetime tool 'get_day_of_week' invoked with date: {date or 'None (using today)'}"
        )
        try:
            if date:
                dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            else:
                dt = datetime.datetime.now()
            result = dt.strftime("%A")
            logger.info(f"Datetime tool 'get_day_of_week' result: {result}")
            return result
        except ValueError as e:
            error_msg = "Invalid date format. Please use YYYY-MM-DD."
            logger.error(f"Error in get_day_of_week: {error_msg}, {str(e)}")
            return error_msg
        except Exception as e:
            logger.exception("Error getting day of week")
            return f"Error getting day of week: {str(e)}"

    def is_weekend(self, date: Optional[str] = None) -> str:
        """
        Check if a given date is a weekend or not.

        Args:
            date: Optional date in YYYY-MM-DD format. Defaults to today.

        Returns:
            String indicating whether the date is a weekend or weekday
        """
        logger.info(
            f"Datetime tool 'is_weekend' invoked with date: {date or 'None (using today)'}"
        )
        try:
            if date:
                dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            else:
                dt = datetime.datetime.now()
            day_of_week = dt.weekday()
            if day_of_week >= 5:  # Saturday (5) or Sunday (6)
                result = f"Yes, {dt.strftime('%Y-%m-%d')} is a weekend ({dt.strftime('%A')})."
            else:
                result = (
                    f"No, {dt.strftime('%Y-%m-%d')} is a weekday ({dt.strftime('%A')})."
                )
            logger.info(f"Datetime tool 'is_weekend' result: {result}")
            return result
        except ValueError as e:
            error_msg = "Invalid date format. Please use YYYY-MM-DD."
            logger.error(f"Error in is_weekend: {error_msg}, {str(e)}")
            return error_msg
        except Exception as e:
            logger.exception("Error checking weekend status")
            return f"Error checking weekend status: {str(e)}"

    def get_date_info(self, date: Optional[str] = None) -> str:
        """
        Get detailed information about a specific date or today.

        Args:
            date: Optional date in YYYY-MM-DD format. Defaults to today.

        Returns:
            Detailed date information including day of week, day of year, week number, etc.
        """
        logger.info(
            f"Datetime tool 'get_date_info' invoked with date: {date or 'None (using today)'}"
        )
        try:
            if date:
                dt = datetime.datetime.strptime(date, "%Y-%m-%d")
            else:
                dt = datetime.datetime.now()

            # Calculate days until next month
            next_month = dt.replace(day=28) + datetime.timedelta(days=4)
            next_month = next_month.replace(day=1)
            days_until_next_month = (next_month - dt).days

            # Calculate days since beginning of year
            start_of_year = dt.replace(month=1, day=1)
            days_since_start_of_year = (dt - start_of_year).days

            result = f"""Date: {dt.strftime("%Y-%m-%d")}
Day of week: {dt.strftime("%A")}
Month: {dt.strftime("%B")}
Day of month: {dt.day}
Day of year: {days_since_start_of_year + 1}
Week number: {dt.isocalendar()[1]}
Days left in month: {days_until_next_month}
Quarter: Q{(dt.month - 1) // 3 + 1}
Is leap year: {"Yes" if ((dt.year % 4 == 0 and dt.year % 100 != 0) or dt.year % 400 == 0) else "No"}"""
            logger.info("Datetime tool 'get_date_info' executed successfully")
            logger.debug(f"Datetime tool 'get_date_info' result: {result}")
            return result
        except ValueError as e:
            error_msg = "Invalid date format. Please use YYYY-MM-DD."
            logger.error(f"Error in get_date_info: {error_msg}, {str(e)}")
            return error_msg
        except Exception as e:
            logger.exception("Error getting date info")
            return f"Error getting date info: {str(e)}"

    def convert_timezone(self, date_time: str, from_zone: str, to_zone: str) -> str:
        """
        Convert date and time between different timezones.

        Args:
            date_time: Date and time in ISO format (YYYY-MM-DDTHH:MM:SS)
            from_zone: Source timezone (e.g., 'UTC', 'US/Eastern', 'Europe/London')
            to_zone: Target timezone (e.g., 'UTC', 'US/Pacific', 'Asia/Tokyo')

        Returns:
            Converted date and time in the target timezone
        """
        logger.info(
            f"Datetime tool 'convert_timezone' invoked with date_time: {date_time}, "
            f"from_zone: {from_zone}, to_zone: {to_zone}"
        )
        try:
            import pytz

            # Parse the input datetime
            dt = datetime.datetime.fromisoformat(date_time)

            # Add timezone info to the datetime object
            source_tz = pytz.timezone(from_zone)
            target_tz = pytz.timezone(to_zone)

            # Localize the datetime to source timezone, then convert to target timezone
            dt_source = source_tz.localize(dt)
            dt_target = dt_source.astimezone(target_tz)

            result = f"""Original: {dt_source.strftime("%Y-%m-%d %H:%M:%S %Z%z")}
Converted: {dt_target.strftime("%Y-%m-%d %H:%M:%S %Z%z")}"""
            logger.info("Datetime tool 'convert_timezone' executed successfully")
            logger.debug(f"Datetime tool 'convert_timezone' result: {result}")
            return result
        except ImportError:
            error_msg = "Error: pytz module not installed. Please install it using 'pip install pytz'."
            logger.error(f"Error in convert_timezone: {error_msg}")
            return error_msg
        except ValueError as e:
            error_msg = (
                "Invalid date format. Please use ISO format (YYYY-MM-DDTHH:MM:SS)."
            )
            logger.error(f"Error in convert_timezone: {error_msg}, {str(e)}")
            return error_msg
        except Exception as e:
            if (
                "pytz" in locals()
                and hasattr(pytz, "exceptions")
                and hasattr(pytz.exceptions, "UnknownTimeZoneError")
            ):
                if isinstance(e, pytz.exceptions.UnknownTimeZoneError):
                    error_msg = "Unknown timezone. Please use valid timezone names like 'UTC', 'US/Eastern', etc."
                    logger.error(f"Error in convert_timezone: {error_msg}, {str(e)}")
                    return error_msg
            logger.exception("Error in timezone conversion")
            return f"Error converting timezone: {str(e)}"

    def run(self, transport: str = "stdio"):
        """Run the server with the specified transport."""
        self.mcp.run(transport=transport)


async def serve():
    """
    Initialize and run the datetime server.
    """
    server = Server("datetime-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available date and time tools."""
        return [
            Tool(
                name=DateTimeTools.GET_CURRENT_DATE.value,
                description="Get the current date in YYYY-MM-DD format",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name=DateTimeTools.GET_CURRENT_TIME.value,
                description="Get the current time in HH:MM:SS format",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name=DateTimeTools.GET_CURRENT_DATETIME.value,
                description="Get the current date and time in ISO format",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name=DateTimeTools.GET_DAY_OF_WEEK.value,
                description="Get the day of week for a given date or today",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format. If not provided, today's date will be used.",
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name=DateTimeTools.IS_WEEKEND.value,
                description="Check if a given date is a weekend or not",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format. If not provided, today's date will be used.",
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name=DateTimeTools.GET_DATE_INFO.value,
                description="Get detailed information about a specific date or today",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format. If not provided, today's date will be used.",
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name=DateTimeTools.CONVERT_TIMEZONE.value,
                description="Convert date and time between different timezones",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "date_time": {
                            "type": "string",
                            "description": "Date and time in ISO format (YYYY-MM-DDTHH:MM:SS)",
                        },
                        "from_zone": {
                            "type": "string",
                            "description": "Source timezone (e.g., 'UTC', 'US/Eastern', 'Europe/London')",
                        },
                        "to_zone": {
                            "type": "string",
                            "description": "Target timezone (e.g., 'UTC', 'US/Pacific', 'Asia/Tokyo')",
                        },
                    },
                    "required": ["date_time", "from_zone", "to_zone"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls for date and time queries."""
        try:
            datetime_server = DateTimeServer()
            result = ""

            if name == DateTimeTools.GET_CURRENT_DATE.value:
                result = datetime_server.get_current_date()
            elif name == DateTimeTools.GET_CURRENT_TIME.value:
                result = datetime_server.get_current_time()
            elif name == DateTimeTools.GET_CURRENT_DATETIME.value:
                result = datetime_server.get_current_datetime()
            elif name == DateTimeTools.GET_DAY_OF_WEEK.value:
                date = arguments.get("date")
                result = datetime_server.get_day_of_week(date)
            elif name == DateTimeTools.IS_WEEKEND.value:
                date = arguments.get("date")
                result = datetime_server.is_weekend(date)
            elif name == DateTimeTools.GET_DATE_INFO.value:
                date = arguments.get("date")
                result = datetime_server.get_date_info(date)
            elif name == DateTimeTools.CONVERT_TIMEZONE.value:
                if not all(
                    k in arguments for k in ["date_time", "from_zone", "to_zone"]
                ):
                    raise ValueError(
                        "Missing required arguments for timezone conversion"
                    )

                result = datetime_server.convert_timezone(
                    arguments["date_time"], arguments["from_zone"], arguments["to_zone"]
                )
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [TextContent(type="text", text=result)]
        except Exception as e:
            logger.exception(f"Error processing datetime tool call: {str(e)}")
            raise McpError(f"Error processing datetime tool call: {str(e)}")

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
