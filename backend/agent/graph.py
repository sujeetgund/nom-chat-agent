"""
Graph factory for the LangGraph nodes used in the CLI chat loop.
"""

from __future__ import annotations

import logging

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from functools import lru_cache
from .nodes import agent_node, set_tool_status, tools_node
from .state import AgentState
from config import get_settings


def _should_use_tools(state: AgentState) -> str:
    messages = list(state.get("messages", []))
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage) and getattr(
        last_message, "tool_calls", None
    ):
        return "set_status"
    return "end"


def _normalize_database_url(database_url: str) -> str:
    """Normalize database URL for psycopg compatibility."""
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg://")
    if database_url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg2://")
    return database_url


@lru_cache(maxsize=1)
def _make_checkpointer():
    """Create a synchronous Postgres checkpointer."""
    settings = get_settings()
    database_url = _normalize_database_url(settings.database_url)

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool
    except ImportError as exc:
        raise ImportError(
            "langgraph-checkpoint-postgres and psycopg-pool are required for graph checkpointing."
        ) from exc

    logger = logging.getLogger(__name__)

    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": None,
        "row_factory": dict_row,
    }

    pool = ConnectionPool(
        conninfo=database_url,
        kwargs=connection_kwargs,
        min_size=1,
        max_size=10,
        open=False,  # Don't block startup; open lazily
    )
    # Open the pool with a generous timeout so Cloud Run startup isn't blocked
    try:
        pool.open(wait=True, timeout=30.0)
    except Exception as exc:
        logger.error("Failed to open DB connection pool: %s", exc)
        raise

    checkpointer = PostgresSaver(pool)
    try:
        checkpointer.setup()
    except Exception as setup_exc:
        # On Cloud Run, pooled connections may carry stale prepared-statement
        # caches, causing DuplicatePreparedStatement on the first migration
        # query.  Since setup() is idempotent we can safely ignore this.
        import psycopg.errors

        if isinstance(setup_exc, psycopg.errors.DuplicatePreparedStatement):
            logger.warning(
                "Ignoring DuplicatePreparedStatement during setup (tables likely already exist)."
            )
        else:
            raise
    return checkpointer


def build_graph(checkpointer=None):
    if checkpointer is None:
        checkpointer = _make_checkpointer()

    builder = StateGraph(AgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("set_status", set_tool_status)
    builder.add_node("tools", tools_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges(
        "agent",
        _should_use_tools,
        {"set_status": "set_status", "end": END},
    )
    builder.add_edge("set_status", "tools")
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=checkpointer)
