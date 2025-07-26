# GenAI-Cookbook-Intel-Azure
Practice scripts in python to get upto speed using the GenAI azure openai large language models

**NB: Please make sure this repo is in a folder that doesn't have underscores, it will effect the agent's code execution**
# before you start
- Install python 3.12
- Install VS Code
- set up http_proxy, https_proxy and no_proxy in your settings. [Instructions here](https://intelpedia.intel.com/Set_proxy)
- Please make sure this repo is in a folder that doesn't have underscores, it will effect the agent's code execution

# lessons
- [openai_api_basics.ipynb](https://github.com/intel-sandbox/GenAI-Cookbook-Intel-Azure/blob/main/openai_api_basics.ipynb): Code for running all the basic functionality from chat completion, embeddings, playing around with arguments and function calling

- [requirements.txt](https://github.com/intel-sandbox/GenAI-Cookbook-Intel-Azure/blob/main/requirements.txt): required for running the basic scripts.

- [metadata_filter_using_function.ipynb](https://github.com/intel-sandbox/GenAI-Cookbook-Intel-Azure/blob/main/metadata_filter_using_function.ipynb): How to use functions to extract metadata from a query (ChipGPT potential feature - POC)

- [MCP](https://github.com/intel-sandbox/GenAI-Cookbook-Intel-Azure/tree/main/MCP): Model Context Protocol implementation - architecture for connecting LLMs to specialized servers and tools, including a travel itinerary demo and ServiceNow integration.

## Data Digger - A Database Assistant Agent
[database_assistant](https://github.com/intel-sandbox/GenAI-Cookbook-Intel-Azure/tree/main/database_assistant) is the project root directory of the flask UI app.

**To get this running checkout this Installation Readme:**
[Data Digger Readme](https://github.com/intel-sandbox/GenAI-Cookbook-Intel-Azure/tree/main/database_assistant/README.md)


## Note:
**using pre-commits to make sure you dont mess up with the python notebooks:**
pre-commit install

curl -L -o /usr/bin/jq.exe https://github.com/jqlang/jq/releases/latest/download/jq-win64.exe

if you get a permission denied error run the terminal in admin mode.

## Setting up api key.
You need to request an api key from [here]()
once you have the key please put it in a .env file in each folder. The .env file should have the following format:
```
OPENAI_API_KEY=<put your key here>
OPENAI_API_HOST="https://aimsoa.iglb.intel.com/"
```

#### For more details:
Contact: atharva.patade@intel.com
