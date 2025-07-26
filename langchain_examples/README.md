## Langchain & LangGraph
*NOTE: These are random notes for the time being*

### .env vars to setup to run the langchain folder:
[I](mailto:atharva.patade@intel.com) prefer using a .env file
```
export OPENAI_API_KEY="your-api-key"
export OPENAI_API_HOST="your-api-host"
export HTTP_PROXY='http://proxy-chain.intel.com:911'
export HTTPS_PROXY='http://proxy-chain.intel.com:912'
export NO_PROXY='.intel.com,localhost,163.33.7.6,127.0.0.1'
```

*For the following env vars get it from: https://developers.google.com/custom-search/v1/overview and follow the prerequisites section*
*GOOGLE_SEARCH_ENGINE_ID and GOOGLE_CSE_ID are the exact same*

```
export GOOGLE_API_KEY=''
export GOOGLE_SEARCH_ENGINE_ID=''
export GOOGLE_CSE_ID=''
```

The LangChain framework consists of multiple open-source libraries.

Reference: [LangChain Python Docs](https://python.langchain.com/docs/introduction/)

- **langchain-core:** Base abstractions for chat models and other components.
- Integration packages (e.g. langchain-openai, langchain-anthropic, etc.): Important integrations have been split into lightweight packages that are co-maintained by the LangChain team and the integration developers.
- **langchain:** Chains, agents, and retrieval strategies that make up an application's cognitive architecture.
- **langchain-community:** Third-party integrations that are community maintained.
- **langgraph:** Orchestration framework for combining LangChain components into production-ready applications with persistence, streaming, and other key features. See LangGraph documentation.


### Langraph In-built Persistence Layer
[refer doc for persistence layer info](https://langchain-ai.github.io/langgraph/concepts/persistence/)


### Why LangGraph? What does it do?

[LangGraph](https://langchain-ai.github.io/langgraph/) is a low-level orchestration framework for building controllable agents. While langchain provides integrations and composable components to streamline LLM application development, the LangGraph library enables agent orchestration — offering customizable architectures, long-term memory, and human-in-the-loop to reliably handle complex tasks.

---
For more details:
atharva.patade@intel.com
