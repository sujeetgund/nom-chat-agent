"""Research helpers: local KB retrieval plus optional web search.

This module provides two tools:
- `web_search(query, top_k=5)`: DuckDuckGo web search via LangChain utilities.
- `research(topic, top_k=5, use_web=False)`: Combines local KB search with
  optional web search when `use_web=True` or when local results are weak.
"""

from __future__ import annotations

import asyncio
import time
from typing import Tuple

from langchain_core.tools import tool
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper


from .rag import format_search_results, search_knowledge_base


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
    """Perform a DuckDuckGo web search and return formatted results.

    This uses LangChain's `DuckDuckGoSearchAPIWrapper.run()` which returns a
    plain-text summary of results.
    """
    return _web_search_impl(query, top_k)


def _research_impl(topic: str, top_k: int = 5, use_web: bool = False) -> str:
    """Return grounded research notes for a topic.

    Behavior:
    - Always attempt local KB retrieval first.
    - If `use_web=True` or local results are empty/weak, also run `web_search`
      and include the web findings after the KB summary.
    """

    # Local KB retrieval
    hits, retrieval_time_ms = search_knowledge_base(topic, top_k=top_k)
    kb_summary = format_search_results(topic, hits, retrieval_time_ms)

    output_parts = [
        f"Research notes for: {topic}",
        "",
        "Local knowledge-base results:",
        kb_summary,
    ]

    # Determine if we should run web search automatically: run if requested
    # explicitly or if there are no KB hits
    if use_web or not hits:
        web_results = _web_search_impl(topic, top_k=top_k)
        output_parts.extend(["", "Web search results:", web_results])

    return "\n".join(output_parts)


@tool
def research(topic: str, top_k: int = 5, use_web: bool = False) -> str:
    """Return grounded research notes for a topic.

    Behavior:
    - Always attempt local KB retrieval first.
    - If `use_web=True` or local results are empty/weak, also run web search
      and include the web findings after the KB summary.
    """
    return _research_impl(topic, top_k, use_web)
