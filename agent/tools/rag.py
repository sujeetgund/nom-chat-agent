"""Knowledge-base search helpers for the chat agent."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from langchain_core.tools import tool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEARCHABLE_EXTENSIONS = {".md", ".txt", ".py"}


@dataclass(frozen=True)
class SearchHit:
    path: Path
    score: int
    excerpt: str


def _iter_search_files() -> Iterable[Path]:
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SEARCHABLE_EXTENSIONS:
            continue
        if any(part.startswith(".") for part in path.relative_to(PROJECT_ROOT).parts):
            continue
        yield path


def _normalize_terms(text: str) -> list[str]:
    return [term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) > 2]


def _make_excerpt(text: str, terms: list[str], *, width: int = 220) -> str:
    lowered = text.lower()
    positions = [lowered.find(term) for term in terms if lowered.find(term) != -1]
    if positions:
        start = max(min(positions) - width // 2, 0)
    else:
        start = 0
    excerpt = text[start : start + width].replace("\n", " ").strip()
    if start > 0:
        excerpt = f"... {excerpt}"
    if start + width < len(text):
        excerpt = f"{excerpt} ..."
    return excerpt


def search_knowledge_base(query: str, *, top_k: int = 5) -> list[SearchHit]:
    terms = _normalize_terms(query)
    if not terms:
        return []

    hits: list[SearchHit] = []
    for path in _iter_search_files():
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        lower_content = content.lower()
        score = sum(lower_content.count(term) for term in terms)
        if score == 0:
            continue

        hits.append(
            SearchHit(
                path=path.relative_to(PROJECT_ROOT),
                score=score,
                excerpt=_make_excerpt(content, terms),
            )
        )

    hits.sort(key=lambda item: (item.score, -len(str(item.path))), reverse=True)
    return hits[:top_k]


def format_search_results(query: str, hits: list[SearchHit]) -> str:
    if not hits:
        return (
            "No strong matches were found in the local knowledge base for this query.\n"
            "Try rephrasing the question or ask for a proposal/PRD based on the available docs."
        )

    lines = [f"Top matches for: {query}", ""]
    for index, hit in enumerate(hits, start=1):
        lines.append(f"{index}. {hit.path} (score: {hit.score})")
        lines.append(f"   {hit.excerpt}")
    return "\n".join(lines)


@tool
async def rag_search(query: str, top_k: int = 5) -> str:
    """Search the local knowledge base for relevant project context."""

    hits = await asyncio.to_thread(search_knowledge_base, query, top_k=top_k)
    return format_search_results(query, hits)
