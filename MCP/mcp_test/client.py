import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

if load_dotenv():
    logger.info("Environment variables loaded from .env file")
else:
    logger.warning("No .env file found. Ensure environment variables are set.")


async def main():
    logger.info("Starting MCP client")

    try:
        # Instantiate the AzureChatOpenAI model with streaming enabled
        logger.info("Initializing Azure OpenAI model")
        logger.info(f"connection with key:  {os.environ['AZURE_OPENAI_API_KEY']}")
        logger.info(f"connection with host: {os.environ['OPENAI_API_HOST']}")
        model = AzureChatOpenAI(
            azure_endpoint=os.environ["OPENAI_API_HOST"],
            azure_deployment="gpt-4o",
            openai_api_version="2024-11-20",
            streaming=True,
        )
    except KeyError as e:
        logger.error(f"Missing environment variable: {e}")
        print(f"Error: Missing environment variable {e}. Please check your .env file.")
        return
    except Exception as e:
        logger.exception("Error initializing Azure OpenAI model")
        print(f"Error initializing model: {e}")
        return

    # Define MCP server parameters
    server_params = {
        "datetime": {
            "command": "python",
            "args": ["./datetime_server.py"],
            "transport": "stdio",
            "capture_output": True,
            "debug": True,  # Add this for more verbose MCP logging
        },
        "google_search": {
            "command": "python",
            "args": ["./google_search_server.py"],
            "transport": "stdio",
            "capture_output": True,
            "debug": True,
        },
        "weather": {
            "command": "python",
            "args": ["./weather_server.py"],
            "transport": "stdio",
            "capture_output": True,
            "debug": True,
        },
        "calculator": {
            "command": "python",
            "args": ["./calculator_server.py"],
            "transport": "stdio",
            "capture_output": True,
            "debug": True,
        },
    }

    # Connect to the MCP servers
    try:
        logger.info("Connecting to MCP servers")
        async with MultiServerMCPClient(server_params) as client:
            logger.info("Successfully connected to MCP servers")
            tools = client.get_tools()

            # Create a strong system prompt that enforces date awareness
            system_prompt = """You are an AI assistant with access to various tools.

FOR TIME-SENSITIVE QUERIES:
- ALWAYS use the datetime tool to get the current date FIRST before using any other tools
- NEVER use hardcoded dates like "October 2023" in search queries
- ALWAYS include the actual current date in search queries when relevant
- For queries about "today", "current", "latest", "recent" events, you MUST check the current date first

For example, if asked about today's news or weather:
1. First call datetime_get_current_date to determine the current date
2. Use that actual date in your subsequent tool calls (search, weather, etc.)
3. Include the date in your response to clarify the timeframe

Tool usage guidelines:
- Calculator: For mathematical calculations
- Google: For web searches (always include current year/date for current events)
- Weather: For weather forecasts
- Datetime: For current date/time information (use FIRST for time-sensitive queries)
"""

            # Create a reactive agent with the custom system prompt
            logger.info("Creating reactive agent")
            agent = create_react_agent(model, tools, prompt=system_prompt)
            logger.info("Agent created successfully")

            while True:
                user_input = input("\nEnter your query (or type 'exit' to quit): ")
                if user_input.strip().lower() == "exit":
                    logger.info("User requested exit")
                    break

                # Log when we start processing with the agent
                logger.info(f"Invoking agent with query: '{user_input}'")

                try:
                    # Create proper HumanMessage object
                    messages = [HumanMessage(content=user_input)]

                    # Invoke the agent with proper messages format
                    response = await agent.ainvoke({"messages": messages})
                    logger.info("Agent invocation successful.")

                    # Debug the response structure
                    logger.debug(f"Response type: {type(response)}")
                    logger.debug(f"Response content: {response}")

                    # Extract the final output from the AIMessage object
                    final_output = ""

                    if "messages" in response:
                        for message in reversed(response["messages"]):
                            if isinstance(message, AIMessage):
                                final_output = message.content
                                break
                    elif isinstance(response, dict) and "output" in response:
                        final_output = response["output"]
                    elif isinstance(response, AIMessage):
                        # Direct AIMessage response
                        final_output = response.content
                    else:
                        # Fallback to string representation
                        final_output = str(response)

                except Exception as e:
                    logger.error(f"Tool call failed with error: {e}", exc_info=True)
                    print(f"\nTool call failed with error: {e}")
                    continue

                if not final_output:
                    final_output = "I'm sorry, I couldn't come up with an answer based on the available tools."

                # Log the final output
                logger.info(f"AI Response: {final_output}")
                print(f"\nAI Response: {final_output}")

    except Exception as e:
        logger.exception(f"Error connecting to MCP servers: {e}")
        print(f"Error connecting to MCP servers: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
        print("\nProgram terminated by user.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
