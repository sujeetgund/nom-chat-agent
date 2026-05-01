"""
2 nodes architecture: agent and tools nodes
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from .prompts import build_agent_system_prompt
from .state import AgentState
from .tools.common import get_chat_model
from .tools.email import draft_email
from .tools.estimate import estimate_cost
from .tools.prd import generate_prd
from .tools.proposal import generate_proposal
from .tools.rag import rag_search
from .tools.research import research

TOOL_MAP = {
    "rag_search": rag_search,
    "research": research,
    "generate_proposal": generate_proposal,
    "generate_prd": generate_prd,
    "estimate_cost": estimate_cost,
    "draft_email": draft_email,
}

TOOL_STATUS_MAP = {
    "rag_search": "researching",
    "research": "researching",
    "generate_proposal": "writing_proposal",
    "generate_prd": "writing_prd",
    "estimate_cost": "thinking",
    "draft_email": "thinking",
}

ASK_NAME_MESSAGE = "Hi! What is your name?"


def _latest_human_message(messages: list[BaseMessage]) -> HumanMessage | None:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return message
    return None


def _latest_ai_message(messages: list[BaseMessage]) -> AIMessage | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None


def _extract_name(text: str) -> str | None:
    cleaned = text.strip()
    if not cleaned or "?" in cleaned:
        return None

    cleaned = re.sub(r"^(my name is|i am|i'm|im|this is)\s+", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[^A-Za-z0-9 .'-]", "", cleaned).strip()
    words = [word for word in cleaned.split() if word]
    if not words or len(words) > 3:
        return None

    candidate = " ".join(words)
    if candidate.lower() in {"help", "hello", "hi", "thanks", "thank you"}:
        return None
    return candidate


def _is_asking_for_name(message: AIMessage | None) -> bool:
    return bool(message and message.content.strip().lower() == ASK_NAME_MESSAGE.lower())


async def agent_node(state: AgentState) -> dict[str, Any]:
    messages = list(state.get("messages", []))
    user_name = state.get("user_name")

    if not user_name:
        latest_ai = _latest_ai_message(messages)
        if not _is_asking_for_name(latest_ai):
            return {
                "messages": [AIMessage(content=ASK_NAME_MESSAGE)],
                "agent_status": "idle",
            }

        latest_human = _latest_human_message(messages)
        extracted_name = _extract_name(latest_human.content) if latest_human else None
        if extracted_name:
            user_name = extracted_name
        else:
            return {
                "messages": [AIMessage(content=ASK_NAME_MESSAGE)],
                "agent_status": "idle",
            }

    llm = get_chat_model().bind_tools(list(TOOL_MAP.values()))
    prompt = build_agent_system_prompt(user_name)
    response = await llm.ainvoke([SystemMessage(content=prompt)] + messages)

    return {
        "messages": [response],
        "agent_status": "thinking",
        "user_name": user_name,
    }


def set_tool_status(state: AgentState) -> dict[str, str]:
    messages = list(state.get("messages", []))
    last_ai = _latest_ai_message(messages)

    if not last_ai or not getattr(last_ai, "tool_calls", None):
        return {"agent_status": "thinking"}

    first_call = last_ai.tool_calls[0]
    tool_name = first_call.get("name", "")
    return {"agent_status": TOOL_STATUS_MAP.get(tool_name, "thinking")}


async def tools_node(state: AgentState) -> dict[str, Any]:
    messages = list(state.get("messages", []))
    last_ai = _latest_ai_message(messages)
    tool_calls = list(getattr(last_ai, "tool_calls", []) or [])

    tool_messages: list[ToolMessage] = []
    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        tool_fn = TOOL_MAP.get(tool_name)

        if tool_fn is None:
            tool_messages.append(
                ToolMessage(
                    content=f"Unknown tool: {tool_name}",
                    tool_call_id=tool_call.get("id", tool_name),
                )
            )
            continue

        try:
            result = await tool_fn.ainvoke(tool_args)
        except Exception as exc:  # pragma: no cover - surfaced to the CLI
            result = f"Tool error: {exc}"

        tool_messages.append(
            ToolMessage(
                content=result,
                tool_call_id=tool_call.get("id", tool_name),
            )
        )

    return {"messages": tool_messages, "agent_status": "idle"}


"""
2 nodes architecture: agent and tools nodes
"""
