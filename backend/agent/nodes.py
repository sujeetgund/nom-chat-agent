"""
2 nodes architecture: agent and tools nodes
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field

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


class NameExtraction(BaseModel):
    name: str | None = Field(default=None, description="The user's name if provided.")


def _latest_ai_message(messages: list[BaseMessage]) -> AIMessage | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None


def _chunk_to_ai_message(chunk: Any) -> AIMessage:
    return AIMessage(
        content=getattr(chunk, "content", None),
        additional_kwargs=dict(getattr(chunk, "additional_kwargs", {}) or {}),
        response_metadata=dict(getattr(chunk, "response_metadata", {}) or {}),
        tool_calls=list(getattr(chunk, "tool_calls", []) or []),
        id=getattr(chunk, "id", None),
    )


async def _extract_user_name(text: str) -> str | None:
    extractor = get_chat_model().with_structured_output(
        NameExtraction, method="json_schema"
    )
    result = await extractor.ainvoke(
        [
            SystemMessage(
                content=(
                    "Extract the person's name from the message. "
                    "Return null if the message does not clearly contain a name. "
                    "Do not guess."
                )
            ),
            HumanMessage(content=f"Message: {text}"),
        ]
    )
    return result.name.strip() if result.name else None


async def agent_node(state: AgentState) -> dict[str, Any]:
    messages = list(state.get("messages", []))
    user_name = state.get("user_name")

    if not user_name:
        latest_human = next(
            (
                message
                for message in reversed(messages)
                if isinstance(message, HumanMessage)
            ),
            None,
        )

        if latest_human is not None:
            extracted_name = await _extract_user_name(
                str(getattr(latest_human, "content", ""))
            )
            if extracted_name:
                user_name = extracted_name

    llm = get_chat_model().bind_tools(list(TOOL_MAP.values()))
    prompt = build_agent_system_prompt(user_name)
    response = await llm.ainvoke(
        [SystemMessage(content=prompt)] + messages,
        config={"tags": ["main_llm"]}
    )

    result: dict[str, Any] = {
        "messages": [response],
        "agent_status": "thinking",
    }

    if user_name:
        result["user_name"] = user_name

    return result


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
