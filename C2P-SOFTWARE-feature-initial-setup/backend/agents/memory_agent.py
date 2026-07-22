import json
from typing import Any, Dict, List, Optional

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from rag_engine import semantic_search


def search_engineering_memory(query: str, collections: Optional[List[str]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """Return the top semantic search results for an engineering query."""
    if not query or not isinstance(query, str):
        return []

    try:
        results = semantic_search(query, collections=collections, top_k=top_k)
        return results if results is not None else []
    except Exception as e:
        # Fallback gracefully if Qdrant collections are not initialized
        print(f"  [Memory Agent] Qdrant collection unavailable, defaulting to empty context. ({e})")
        return []


memory_agent_tool = FunctionTool(search_engineering_memory)
memory_llm_agent = LlmAgent(
    name="memory_agent",
    description="Search the engineering memory stores and return semantically relevant knowledge for a query.",
    instruction=(
        "Use the search_engineering_memory tool to retrieve relevant memory entries for an engineering query. "
        "Return the top results from available collections."
    ),
    tools=[memory_agent_tool],
)


class memory_agent:
    @staticmethod
    def search_engineering_memory(query: str, collections: Optional[List[str]] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        return search_engineering_memory(query, collections=collections, top_k=top_k)