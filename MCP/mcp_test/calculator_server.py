# calculator_server.py
import logging

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Create the MCP server instance named "Calculator"
mcp = FastMCP("Calculator")


@mcp.tool()
def add(a: float, b: float) -> float:
    logger.info(f"Tool 'add' invoked with a={a}, b={b}")
    result = a + b
    logger.info(f"Tool 'add' returning result={result}")
    return result


@mcp.tool()
def subtract(a: float, b: float) -> float:
    logger.info(f"Tool 'subtract' invoked with a={a}, b={b}")
    result = a - b
    logger.info(f"Tool 'subtract' returning result={result}")
    return result


@mcp.tool()
def multiply(a: float, b: float) -> float:
    logger.info(f"Tool 'multiply' invoked with a={a}, b={b}")
    result = a * b
    logger.info(f"Tool 'multiply' returning result={result}")
    return result


@mcp.tool()
def divide(a: float, b: float) -> float:
    logger.info(f"Tool 'divide' invoked with a={a}, b={b}")
    if b == 0:
        logger.error("Tool 'divide' encountered division by zero.")
        return "Error: Division by zero"
    result = a / b
    logger.info(f"Tool 'divide' returning result={result}")
    return result


if __name__ == "__main__":
    mcp.run(transport="stdio")
