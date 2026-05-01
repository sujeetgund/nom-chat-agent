"""Research helper built on top of the local knowledge-base search."""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool

from .rag import format_search_results, search_knowledge_base


@tool
async def research(topic: str, top_k: int = 5) -> str:
    """Return grounded research notes for a topic."""

    hits = await asyncio.to_thread(search_knowledge_base, topic, top_k=top_k)
    summary = format_search_results(topic, hits)
    return f"Research notes for: {topic}\n\n{summary}"
