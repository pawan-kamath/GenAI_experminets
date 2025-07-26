import asyncio
import logging
import os

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    # Define MCP server parameters
    server_params = {
        "knowledge": {
            "command": "python",
            "args": ["snow_server.py"],
            "transport": "stdio",
        }
    }

    # Instantiate the AzureChatOpenAI model
    model = AzureChatOpenAI(
        azure_endpoint=os.environ["OPENAI_API_HOST"],
        azure_deployment="gpt-4o",
        openai_api_version="2024-11-20",
        streaming=True,
    )

    # Connect to the MCP server
    async with MultiServerMCPClient(server_params) as client:
        tools = client.get_tools()
        # Create a reactive agent using the model and tools
        agent = create_react_agent(model, tools)

        while True:
            user_input = input("Enter your query (or type 'exit' to quit): ").strip()
            if user_input.lower() == "exit":
                logger.info("User exited the application.")
                break

            logger.info(f"User input: {user_input}")
            print(f"\nHuman Message: {user_input}")
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


if __name__ == "__main__":
    asyncio.run(main())
