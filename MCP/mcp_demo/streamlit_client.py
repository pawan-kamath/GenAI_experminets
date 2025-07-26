import asyncio
import logging
import os
import sys

# Use ProactorEventLoop on Windows for subprocess compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
if load_dotenv():
    logger.info("Environment variables loaded from .env file")
else:
    logger.warning("No .env file found. Ensure environment variables are set.")

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


def extract_final_ai_response(response):
    """Extract the final AI response from the complex message structure."""
    try:
        # If the response is already a string, return it directly
        if isinstance(response, str):
            return response

        # Handle dictionary response with "messages" key
        if isinstance(response, dict) and "messages" in response:
            messages = response["messages"]

            # Find the last AIMessage with content
            for msg in reversed(messages):
                # Check if it's an AIMessage object with content
                if isinstance(msg, AIMessage) and msg.content:
                    return msg.content

                # Check if it's a dictionary representation and has content
                if isinstance(msg, dict) and msg.get("content"):
                    # Check for AIMessage type markers
                    if msg.get("type") == "ai" or (
                        msg.get("id", "").startswith("run-")
                        and "tool_call" not in msg.get("id", "")
                    ):
                        return msg["content"]

            # If nothing found, return the entire response as a fallback
            return str(response)

        # For responses from the agent.ainvoke
        if hasattr(response, "content") and isinstance(response, AIMessage):
            return response.content

        # Handle dictionary with "output" key
        if isinstance(response, dict) and "output" in response:
            return response["output"]

        # Final fallback
        return str(response)

    except Exception as e:
        logger.error(f"Error extracting AI response: {e}", exc_info=True)
        return f"Error processing response: {str(e)}"


async def run_agent(query):
    try:
        # Initialize the Azure OpenAI model
        model = AzureChatOpenAI(
            azure_endpoint=os.environ["OPENAI_API_HOST"],
            azure_deployment="gpt-4o",
            openai_api_version="2024-11-20",
            streaming=True,
        )

        # Connect to the MCP servers
        async with MultiServerMCPClient(server_params) as client:
            tools = client.get_tools()

            # Create a system prompt for the agent
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
            agent = create_react_agent(model, tools, prompt=system_prompt)

            # Create proper HumanMessage object
            messages = [HumanMessage(content=query)]

            # Invoke the agent and return the full response object
            return await agent.ainvoke({"messages": messages})

    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        return f"Error: {e}"


def main():
    st.title("Travel Itinerary Assistant")

    # Input box for user query
    query = st.text_input("Enter your query:", "")

    if st.button("Submit"):
        if query.strip():
            with st.spinner("Processing..."):
                # Run the agent and get the raw response
                raw_response = asyncio.run(run_agent(query))

                # Extract the final AI response
                final_response = extract_final_ai_response(raw_response)

                # Display the clean response
                st.markdown(final_response, unsafe_allow_html=True)
        else:
            st.warning("Please enter a query before submitting.")


if __name__ == "__main__":
    main()
