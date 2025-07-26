import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

loaded = load_dotenv(override=True)
if loaded:
    print("Environment variables loaded successfully.")
else:
    print("Failed to load environment variables.")

api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = "2024-07-01-preview"
azure_host = os.getenv("AZURE_OPENAI_HOST")
print(f"api_key:{api_key}, api_version: {api_version}, azure_host: {azure_host}")


# Initialize the AzureChatOpenAI object with custom host
gpt4o_chat = AzureChatOpenAI(
    azure_endpoint=azure_host,
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key,
    api_version="2024-05-01-preview",
)
print(gpt4o_chat)
# Test the model with a simple prompt
response = gpt4o_chat("What is the capital of France?")
print(response)
