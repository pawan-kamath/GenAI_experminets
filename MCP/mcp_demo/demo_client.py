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
    logger.info("Starting Travel Itinerary MCP client")

    try:
        # Instantiate the AzureChatOpenAI model with streaming enabled
        logger.info("Initializing Azure OpenAI model")
        logger.info("Azure OpenAI API Host: %s", os.environ.get("OPENAI_API_HOST"))
        logger.info("Azure OpenAI API Key: %s", os.environ.get("AZURE_OPENAI_API_KEY"))

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
        "google_search": {
            "command": "python",
            "args": ["./google_search_server.py"],
            "transport": "stdio",
            "capture_output": True,
        },
        "calculator": {
            "command": "python",
            "args": ["./calculator_server.py"],
            "transport": "stdio",
            "capture_output": True,
        },
        "gocar": {
            "command": "python",
            "args": ["./gocar_server.py"],
            "transport": "stdio",
            "capture_output": True,
        },
        "weather": {
            "command": "python",
            "args": ["./weather_server.py"],
            "transport": "stdio",
            "capture_output": True,
        },
        "datetime": {
            "command": "python",
            "args": ["./datetime_server.py"],
            "transport": "stdio",
            "capture_output": True,
        },
    }

    # Connect to the MCP servers
    try:
        logger.info("Connecting to MCP servers")
        async with MultiServerMCPClient(server_params) as client:
            logger.info("Successfully connected to MCP servers")
            tools = client.get_tools()

            # Create a system prompt that emphasizes travel planning and tool usage
            system_prompt = """You are a helpful travel assistant with access to various tools that can help plan the perfect trip.

ALWAYS use the appropriate tools when information is needed:
- Google Search: For finding places to visit, attractions, restaurants, and general travel information
- Weather: For checking weather forecasts at travel destinations
- GoCar: For finding available car types and rental rates
- Calculator: For any calculations needed during trip planning

TRAVEL PLANNING GUIDELINES:
- Structure itineraries by day with morning, afternoon, and evening activities
- Include a mix of popular attractions and local experiences
- Consider travel times between locations
- Adjust recommendations based on weather forecasts
- Provide car rental options when transportation is needed
- Calculate estimated costs when possible

When creating a multi-day itinerary:
1. First research the destination using Google Search
2. Check the weather forecast to plan appropriate activities
3. Consider transportation needs and recommend suitable car options if needed
4. Present a clear, organized itinerary with estimated times and costs
5. Format your response in a clean, readable way with clear headings and sections

Remember to be thorough in your research and thoughtful in your recommendations.
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
