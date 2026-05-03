"""Web search tool using DuckDuckGo."""

from __future__ import annotations

import time

from langchain_core.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


def _web_search_impl(query: str, top_k: int = 5) -> str:
    """Perform a DuckDuckGo web search and return formatted results.

    This uses LangChain's `DuckDuckGoSearchAPIWrapper.run()` which returns a
    plain-text summary of results.
    """
    wrapper = DuckDuckGoSearchAPIWrapper()
    start = time.time()
    try:
        results_text = wrapper.run(query)
    except Exception as e:
        return f"Web search failed: {e}"

    elapsed = (time.time() - start) * 1000
    header = f"Web search results for: {query}\n(Retrieved in {elapsed:.0f}ms)\n\n"
    # Truncate extremely large responses for tool output
    return header + (
        results_text[:10000] + "..." if len(results_text) > 10000 else results_text
    )


@tool
def web_search(query: str, top_k: int = 5) -> str:
    """Search the web using DuckDuckGo for current information, market data, or topics not in the local knowledge base.

    Args:
        query: The search query
        top_k: Number of results to return (default 5)

    Returns:
        Formatted web search results.
    """
    return _web_search_impl(query, top_k)
