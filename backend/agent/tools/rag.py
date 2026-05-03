"""Knowledge-base search helpers using pgvector embeddings."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import psycopg
from langchain_core.tools import tool
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpointEmbeddings

from config import get_settings, AVAILABLE_SOURCE_TYPES
import json


@dataclass(frozen=True)
class SearchHit:
    content: str
    metadata: dict[str, Any]
    similarity: float
    retrieval_time_ms: float


def _get_embeddings_model() -> HuggingFaceEmbeddings:
    """Get the embeddings model."""
    settings = get_settings()
    return HuggingFaceEndpointEmbeddings(
        model=settings.hf_embedding_model,
        huggingfacehub_api_token=settings.hf_api_token,
    )


def search_knowledge_base(
    query: str, *, source_type: str | None = None, top_k: int = 5
) -> tuple[list[SearchHit], float]:
    """
    Search pgvector for relevant documents using embedding similarity.

    Args:
        query: The search query
        source_type: Optional filter by document type (e.g. 'service', 'case_study', 'blog', 'company')
                    If None, searches across all types.
        top_k: Number of results to return (default 5)

    Returns:
        (hits, total_retrieval_time_ms)
    """
    start_time = time.time()
    settings = get_settings()

    # Generate query embedding
    embeddings_model = _get_embeddings_model()
    query_embedding = embeddings_model.embed_query(query)
    # asyncpg expects text for bound params; serialize the vector to Postgres array-like
    # string format accepted by pgvector (e.g. "[0.1,0.2,...]")
    query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # Build SQL with optional source_type filter
            where_clause = "WHERE (metadata->>'source_type') = %s" if source_type else ""
            search_query = f"""
                SELECT content, metadata, 
                       1 - (embedding <=> %s::vector) as similarity
                FROM website_embeddings
                {where_clause}
                ORDER BY embedding <=> %s::vector
                LIMIT %s;
            """

            if source_type:
                cur.execute(
                    search_query, (query_embedding_str, source_type, query_embedding_str, top_k)
                )
            else:
                cur.execute(search_query, (query_embedding_str, query_embedding_str, top_k))
            
            rows = cur.fetchall()

        hits: list[SearchHit] = []
        for row in rows:
            raw_meta = row["metadata"]
            if isinstance(raw_meta, str):
                try:
                    meta = json.loads(raw_meta)
                except Exception:
                    meta = {"raw": raw_meta}
            else:
                meta = raw_meta or {}

            hits.append(
                SearchHit(
                    content=row["content"],
                    metadata=meta,
                    similarity=row["similarity"],
                    retrieval_time_ms=0,  # Will be set after all retrieval
                )
            )

    # Connection closes automatically due to 'with' block

    total_time_ms = (time.time() - start_time) * 1000

    # Update retrieval time for each hit
    hits = [
        SearchHit(
            content=hit.content,
            metadata=hit.metadata,
            similarity=hit.similarity,
            retrieval_time_ms=total_time_ms,
        )
        for hit in hits
    ]

    return hits, total_time_ms


def format_search_results(
    query: str, hits: list[SearchHit], retrieval_time_ms: float
) -> str:
    """Format search results for display."""
    if not hits:
        return (
            "No strong matches were found in the local knowledge base for this query.\n"
            "Try rephrasing the question or ask for a proposal/PRD based on the available docs."
        )

    lines = [
        f"Top matches for: {query}",
        f"(Retrieved in {retrieval_time_ms:.0f}ms)",
        "",
    ]
    for index, hit in enumerate(hits, start=1):
        source = hit.metadata.get("url", "unknown")
        title = hit.metadata.get("title", "Untitled")
        sim_pct = hit.similarity * 100

        lines.append(f"{index}. {title}")
        lines.append(f"   source: {source} (similarity: {sim_pct:.1f}%)")
        lines.append(f"   {hit.content[:200]}...")
        lines.append("")

    return "\n".join(lines)


@tool
def rag_search(query: str, source_type: str | None = None, top_k: int = 5) -> str:
    """Search the local knowledge base for relevant project context using embeddings.

    Args:
        query: The search query
        source_type: Optional filter by document type. Available options: 'service', 'case_study', 'blog', 'company'.
                    If not provided, searches across all document types.
        top_k: Number of results to return (default 5)

    Returns:
        Formatted search results with titles, URLs, similarity scores, and content preview.
    """
    hits, retrieval_time_ms = search_knowledge_base(
        query, source_type=source_type, top_k=top_k
    )
    return format_search_results(query, hits, retrieval_time_ms)
