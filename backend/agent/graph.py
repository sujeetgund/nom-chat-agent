"""
Graph factory for the LangGraph nodes used in the CLI chat loop.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from .nodes import agent_node, set_tool_status, tools_node
from .state import AgentState


def _should_use_tools(state: AgentState) -> str:
    messages = list(state.get("messages", []))
    last_message = messages[-1] if messages else None

    if isinstance(last_message, AIMessage) and getattr(
        last_message, "tool_calls", None
    ):
        return "set_status"
    return "end"


def build_graph(checkpointer):
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
