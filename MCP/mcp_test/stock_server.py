#!/usr/bin/env python
# stock_server.py

import logging

import dotenv
import matplotlib.pyplot as plt
import yfinance as yf
from mcp.server.fastmcp import FastMCP

dotenv.load_dotenv()  # Load environment variables from .env file if needed

logger = logging.getLogger(__name__)

# Create the MCP server instance named "StockAPI"
mcp = FastMCP("StockAPI")


@mcp.tool()
def get_stock_price(ticker: str) -> str:
    """
    Retrieve the latest closing price for the given stock ticker using yfinance.
    """
    try:
        logger.info(f"get_stock_price invoked for ticker: {ticker}")
        t = yf.Ticker(ticker)
        history = t.history(period="1d")
        if not history.empty:
            latest = history["Close"].iloc[-1]
            result = f"The latest price for {ticker.upper()} is {latest:.2f}."
            logger.info(result)
            return result
        result = f"No recent price data available for {ticker.upper()}."
        logger.info(result)
        return result
    except Exception as e:
        logger.exception(f"Error retrieving price for {ticker.upper()}")
        return f"Error retrieving price for {ticker.upper()}: {str(e)}"


@mcp.tool()
def get_earnings_dates(ticker: str) -> str:
    """
    Retrieve earnings date information using the ticker's calendar data.
    """
    try:
        logger.info(f"get_earnings_dates invoked for ticker: {ticker}")
        t = yf.Ticker(ticker)
        cal = t.calendar
        if cal is not None and not cal.empty:
            result = cal.to_string()
            logger.info(f"get_earnings_dates result: {result}")
            return result
        result = f"No earnings date information available for {ticker.upper()}."
        logger.info(result)
        return result
    except Exception as e:
        logger.exception(f"Error retrieving earnings dates for {ticker.upper()}")
        return f"Error retrieving earnings dates for {ticker.upper()}: {str(e)}"


@mcp.tool()
def get_quarterly_earnings(ticker: str) -> str:
    """
    Retrieve quarterly earnings information.
    """
    try:
        logger.info(f"get_quarterly_earnings invoked for ticker: {ticker}")
        t = yf.Ticker(ticker)
        quarterly = t.quarterly_earnings
        if quarterly is not None and not quarterly.empty:
            result = quarterly.to_string()
            logger.info(f"get_quarterly_earnings result: {result}")
            return result
        result = f"No quarterly earnings data available for {ticker.upper()}."
        logger.info(result)
        return result
    except Exception as e:
        logger.exception(f"Error retrieving quarterly earnings for {ticker.upper()}")
        return f"Error retrieving quarterly earnings for {ticker.upper()}: {str(e)}"


@mcp.tool()
def get_stock_history(ticker: str, start_date: str, end_date: str) -> str:
    """
    Retrieve historical closing prices for the given date range.
    Dates should be strings in the format 'YYYY-MM-DD'.
    """
    try:
        logger.info(
            f"get_stock_history invoked for ticker: {ticker} from {start_date} to {end_date}"
        )
        t = yf.Ticker(ticker)
        hist = t.history(start=start_date, end=end_date)
        if not hist.empty:
            closing_prices = hist["Close"]
            # Use .items() instead of iteritems() for compatibility with modern pandas
            lines = [
                f"{index.date()}: {price:.2f}"
                for index, price in closing_prices.items()
            ]
            result = "\n".join(lines)
            logger.info(f"get_stock_history result: {result}")
            return result
        result = f"No historical data available for {ticker.upper()} in the given date range."
        logger.info(result)
        return result
    except Exception as e:
        logger.exception(f"Error retrieving historical data for {ticker.upper()}")
        return f"Error retrieving historical data for {ticker.upper()}: {str(e)}"


@mcp.tool()
def get_stock_plot(ticker: str, start_date: str, end_date: str) -> str:
    """
    Generate a plot of closing prices for the given date range and save it as a PNG file.
    Returns the filename if successful.
    """
    try:
        logger.info(
            f"get_stock_plot invoked for ticker: {ticker} from {start_date} to {end_date}"
        )
        t = yf.Ticker(ticker)
        hist = t.history(start=start_date, end=end_date)
        if not hist.empty:
            plt.figure(figsize=(10, 6))
            plt.plot(hist.index, hist["Close"], label="Close Price")
            plt.title(f"{ticker.upper()} Closing Prices")
            plt.xlabel("Date")
            plt.ylabel("Price (USD)")
            plt.legend()
            file_name = f"{ticker.upper()}_plot.png"
            plt.savefig(file_name)
            plt.close()
            result = f"Plot saved as {file_name}"
            logger.info(result)
            return result
        result = (
            f"No data to generate plot for {ticker.upper()} in the given date range."
        )
        logger.info(result)
        return result
    except Exception as e:
        logger.exception(f"Error generating plot for {ticker.upper()}")
        return f"Error generating plot for {ticker.upper()}: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
