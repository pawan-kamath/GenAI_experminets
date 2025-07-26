import logging
from collections.abc import Sequence
from enum import Enum
from typing import Any

from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool

logger = logging.getLogger(__name__)


class GoCarTools(str, Enum):
    """Enumeration of all GoCar tools available in the server."""

    GET_CAR_TYPES = "get_car_types"
    GET_RATE_BY_CAR_TYPE = "get_rate_by_car_type"
    CALCULATE_RENTAL_COST = "calculate_rental_cost"


class GoCarServer:
    """
    A server that provides information about GoCar rental services.
    """

    def __init__(self, name: str = "GoCar"):
        self.name = name
        self.mcp = FastMCP(name)
        self.setup_tools()

        # Car types and their details
        self.car_types = {
            "GoLocal": {
                "description": "The new baby on our fleet, perfect for short trips around town",
                "models": ["Hyundai i10"],
                "hourly_rate": 9,
                "daily_rate": 50,
                "automatic_option": True,
                "automatic_hourly_extra": 1,
                "automatic_daily_extra": 5,
            },
            "GoCity": {
                "description": "Small cars, perfect for city driving",
                "models": ["Hyundai i20", "Renault Clio", "Nissan Micra"],
                "hourly_rate": 11,
                "daily_rate": 55,
                "automatic_option": True,
                "automatic_hourly_extra": 1,
                "automatic_daily_extra": 5,
            },
            "GoTripper": {
                "description": "Larger hatchbacks to fit more into your day",
                "models": ["Skoda Scala", "Hyundai i30", "Volkswagen T-Cross"],
                "hourly_rate": 12,
                "daily_rate": 60,
                "automatic_option": True,
                "automatic_hourly_extra": 1,
                "automatic_daily_extra": 5,
            },
            "GoExplore": {
                "description": "Subcompact crossover SUVs, perfect for those longer journeys with extra space",
                "models": [
                    "Renault Captur",
                    "Skoda Kamiq",
                    "Hyundai Kona",
                    "Volkswagen T-Roc",
                ],
                "hourly_rate": 13,
                "daily_rate": 65,
                "automatic_option": True,
                "automatic_hourly_extra": 1,
                "automatic_daily_extra": 5,
            },
            "GoExplore PLUS": {
                "description": "New larger SUV vehicles with additional space and comfort for those longer journeys",
                "models": ["Seat Ateca"],
                "hourly_rate": 15,
                "daily_rate": 80,
                "automatic_option": True,
                "automatic_hourly_extra": 1,
                "automatic_daily_extra": 5,
                "free_kms": 75,  # Extra free kilometers
            },
            "GoVan": {
                "description": "Get your job done in a small vans with plenty of space",
                "models": ["Citroen Berlingo"],
                "hourly_rate": 12,
                "daily_rate": 60,
                "automatic_option": False,
            },
            "GoCargo": {
                "description": "Larger vans with space galore. The perfect solution for a any job!",
                "models": ["Renault Traffic", "Ford Transit Custom"],
                "hourly_rate": 15,
                "daily_rate": 75,
                "automatic_option": False,
            },
            "GoElectric": {
                "description": "Fully electric vehicle with automatic transmission",
                "models": ["Hyundai Kona Electric"],
                "hourly_rate": 14,
                "daily_rate": 70,
                "automatic_option": True,  # Already automatic
                "is_automatic": True,
            },
        }

    def setup_tools(self):
        """Register all tools with the MCP server."""
        self.mcp.tool()(self.get_car_types)
        self.mcp.tool()(self.get_rate_by_car_type)
        self.mcp.tool()(self.calculate_rental_cost)

    def get_car_types(self) -> str:
        """
        Get a list of all available car types and their details.

        Returns:
            A formatted string with details about all car types.
        """
        try:
            logger.info("GoCar tool 'get_car_types' invoked")
            result = "Available GoCar rental types:\n\n"

            for car_type, details in self.car_types.items():
                models = ", ".join(details["models"])
                result += f"## {car_type}\n"
                result += f"Description: {details['description']}\n"
                result += f"Models: {models}\n"
                result += f"Hourly rate: €{details['hourly_rate']}/hour\n"
                result += f"Daily rate: €{details['daily_rate']}/day\n"

                if details.get("automatic_option", False):
                    if car_type == "GoElectric":
                        result += "Transmission: Automatic (included in price)\n"
                    else:
                        result += (
                            f"Automatic transmission: Available for additional "
                            f"€{details['automatic_hourly_extra']}/hour or €{details['automatic_daily_extra']}/day\n"
                        )
                else:
                    result += "Automatic transmission: Not available\n"

                if "free_kms" in details:
                    result += f"Free kilometers: {details['free_kms']} km (standard is 50 km)\n"
                else:
                    result += "Free kilometers: 50 km (€0.25 per additional km)\n"

                result += "\n"

            result += "Note: For all rentals, the daily rate applies after 6 hours of use. Each booking includes 50 free kilometers (75 km for GoExplore PLUS), with additional kilometers charged at €0.25/km."

            logger.debug("GoCar tool 'get_car_types' result generated")
            return result

        except Exception as e:
            logger.exception("Error getting car types")
            return f"Error retrieving car type information: {str(e)}"

    def get_rate_by_car_type(self, car_type: str) -> str:
        """
        Get detailed rate information for a specific car type.

        Args:
            car_type: The type of car to get rates for.

        Returns:
            A formatted string with detailed rate information.
        """
        logger.info(
            f"GoCar tool 'get_rate_by_car_type' invoked with car_type: {car_type}"
        )
        try:
            if car_type not in self.car_types:
                available_types = ", ".join(self.car_types.keys())
                return f"Car type '{car_type}' not found. Available car types are: {available_types}"

            details = self.car_types[car_type]
            models = ", ".join(details["models"])

            result = f"# {car_type} Rate Information\n\n"
            result += f"Description: {details['description']}\n"
            result += f"Models: {models}\n\n"

            result += "## Rates\n"
            result += f"Hourly rate: €{details['hourly_rate']}/hour\n"
            result += f"Daily rate: €{details['daily_rate']}/day\n"

            if details.get("automatic_option", False):
                if car_type == "GoElectric":
                    result += "Automatic transmission: Included in price\n"
                else:
                    result += (
                        f"Automatic transmission: Additional €{details['automatic_hourly_extra']}/hour or "
                        f"€{details['automatic_daily_extra']}/day\n"
                    )
            else:
                result += "Automatic transmission: Not available\n"

            result += "\n## Additional Information\n"
            if "free_kms" in details:
                result += f"Free kilometers: {details['free_kms']} km\n"
            else:
                result += "Free kilometers: 50 km\n"

            result += "Additional kilometers: €0.25/km\n"
            result += "Daily rate applies for rentals over 6 hours\n"

            logger.info("GoCar tool 'get_rate_by_car_type' executed successfully")
            return result

        except Exception as e:
            logger.exception(f"Error getting rate for car type: {car_type}")
            return f"Error retrieving rate information: {str(e)}"

    def calculate_rental_cost(
        self,
        car_type: str,
        hours: int = 0,
        days: int = 0,
        kilometers: int = 50,
        automatic: bool = False,
    ) -> str:
        """
        Calculate the total cost of a car rental based on the provided parameters.

        Args:
            car_type: The type of car to rent.
            hours: Number of hours to rent (if less than a day).
            days: Number of days to rent.
            kilometers: Total kilometers expected to drive.
            automatic: Whether an automatic transmission is requested.

        Returns:
            A formatted string with the total cost breakdown.
        """
        logger.info(
            f"GoCar tool 'calculate_rental_cost' invoked with car_type: {car_type}, hours: {hours}, "
            f"days: {days}, kilometers: {kilometers}, automatic: {automatic}"
        )
        try:
            if car_type not in self.car_types:
                available_types = ", ".join(self.car_types.keys())
                return f"Car type '{car_type}' not found. Available car types are: {available_types}"

            details = self.car_types

            # Check if automatic is available for this car type
            if (
                automatic
                and not details.get("automatic_option", False)
                and car_type != "GoElectric"
            ):
                return f"Automatic transmission is not available for {car_type}"

            total_cost = 0
            cost_breakdown = []

            # Handle GoElectric which is always automatic
            is_automatic = automatic
            if car_type == "GoElectric":
                is_automatic = True

            # Calculate base rental cost
            if days > 0:
                total_days_cost = days * details["daily_rate"]
                cost_breakdown.append(
                    f"Base daily rate: {days} days × €{details['daily_rate']} = €{total_days_cost}"
                )
                total_cost += total_days_cost

                # Add automatic transmission cost if needed
                if (
                    is_automatic
                    and car_type != "GoElectric"
                    and details.get("automatic_option", False)
                ):
                    auto_cost = days * details["automatic_daily_extra"]
                    cost_breakdown.append(
                        f"Automatic transmission: {days} days × €{details['automatic_daily_extra']} = €{auto_cost}"
                    )
                    total_cost += auto_cost

            if hours > 0:
                # Check if daily rate should apply (over 6 hours)
                if hours >= 6:
                    cost_breakdown.append(
                        f"Hourly rental exceeds 6 hours. Daily rate applies: €{details['daily_rate']}"
                    )
                    total_cost += details["daily_rate"]

                    # Add automatic transmission cost if needed
                    if (
                        is_automatic
                        and car_type != "GoElectric"
                        and details.get("automatic_option", False)
                    ):
                        cost_breakdown.append(
                            f"Automatic transmission daily rate: €{details['automatic_daily_extra']}"
                        )
                        total_cost += details["automatic_daily_extra"]
                else:
                    hourly_cost = hours * details["hourly_rate"]
                    cost_breakdown.append(
                        f"Hourly rate: {hours} hours × €{details['hourly_rate']} = €{hourly_cost}"
                    )
                    total_cost += hourly_cost

                    # Add automatic transmission cost if needed
                    if (
                        is_automatic
                        and car_type != "GoElectric"
                        and details.get("automatic_option", False)
                    ):
                        auto_cost = hours * details["automatic_hourly_extra"]
                        cost_breakdown.append(
                            f"Automatic transmission: {hours} hours × €{details['automatic_hourly_extra']} = €{auto_cost}"
                        )
                        total_cost += auto_cost

            # Calculate kilometer costs
            free_kms = details.get("free_kms", 50)
            if kilometers > free_kms:
                extra_kms = kilometers - free_kms
                km_cost = extra_kms * 0.25
                cost_breakdown.append(
                    f"Additional kilometers: {extra_kms} km × €0.25 = €{km_cost}"
                )
                total_cost += km_cost
            else:
                cost_breakdown.append(
                    f"Kilometers: {kilometers} km (within the free {free_kms} km allowance)"
                )

            # Format the result
            result = f"# Rental Cost Calculation for {car_type}\n\n"
            result += "## Cost Breakdown\n"
            for item in cost_breakdown:
                result += f"- {item}\n"

            result += f"\n## Total Cost: €{total_cost}\n"

            # Add additional information
            result += "\nNote: Daily rate applies for rentals over 6 hours. Each booking includes free kilometers (50 km standard, 75 km for GoExplore PLUS), with additional kilometers charged at €0.25/km."

            logger.info("GoCar tool 'calculate_rental_cost' executed successfully")
            return result

        except Exception as e:
            logger.exception("Error calculating rental cost")
            return f"Error calculating rental cost: {str(e)}"

    def run(self, transport: str = "stdio"):
        """Run the server with the specified transport."""
        self.mcp.run(transport=transport)


async def serve():
    """
    Initialize and run the GoCar server.
    """
    server = Server("gocar-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available GoCar tools."""
        return [
            Tool(
                name=GoCarTools.GET_CAR_TYPES.value,
                description="Get a list of all available car types and their details",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            ),
            Tool(
                name=GoCarTools.GET_RATE_BY_CAR_TYPE.value,
                description="Get detailed rate information for a specific car type",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "car_type": {
                            "type": "string",
                            "description": "The type of car to get rates for (e.g., GoLocal, GoCity, GoTripper, etc.)",
                        }
                    },
                    "required": ["car_type"],
                },
            ),
            Tool(
                name=GoCarTools.CALCULATE_RENTAL_COST.value,
                description="Calculate the total cost of a car rental based on the provided parameters",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "car_type": {
                            "type": "string",
                            "description": "The type of car to rent (e.g., GoLocal, GoCity, GoTripper, etc.)",
                        },
                        "hours": {
                            "type": "integer",
                            "description": "Number of hours to rent (if less than a day)",
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to rent",
                        },
                        "kilometers": {
                            "type": "integer",
                            "description": "Total kilometers expected to drive",
                        },
                        "automatic": {
                            "type": "boolean",
                            "description": "Whether an automatic transmission is requested",
                        },
                    },
                    "required": ["car_type"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """Handle tool calls for GoCar queries."""
        try:
            gocar_server = GoCarServer()
            result = ""

            if name == GoCarTools.GET_CAR_TYPES.value:
                result = gocar_server.get_car_types()
            elif name == GoCarTools.GET_RATE_BY_CAR_TYPE.value:
                if "car_type" not in arguments:
                    raise ValueError("Missing required argument: car_type")
                result = gocar_server.get_rate_by_car_type(arguments["car_type"])
            elif name == GoCarTools.CALCULATE_RENTAL_COST.value:
                if "car_type" not in arguments:
                    raise ValueError("Missing required argument: car_type")

                car_type = arguments["car_type"]
                hours = arguments.get("hours", 0)
                days = arguments.get("days", 0)
                kilometers = arguments.get("kilometers", 50)
                automatic = arguments.get("automatic", False)

                result = gocar_server.calculate_rental_cost(
                    car_type=car_type,
                    hours=hours,
                    days=days,
                    kilometers=kilometers,
                    automatic=automatic,
                )
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [TextContent(type="text", text=result)]
        except Exception as e:
            logger.exception(f"Error processing GoCar tool call: {str(e)}")
            raise McpError(f"Error processing GoCar tool call: {str(e)}")

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
