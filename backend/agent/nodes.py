"""
2 nodes architecture: agent and tools nodes
"""

from __future__ import annotations

import json
import logging
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
from .tools.prd import generate_prd, generate_proposal
from .tools.rag import rag_search
from .tools.web_search import web_search
from .tools.company_info import fetch_company_info

logger = logging.getLogger(__name__)

TOOL_MAP = {
    "rag_search": rag_search,
    "web_search": web_search,
    "generate_proposal": generate_proposal,
    "generate_prd": generate_prd,
    "fetch_company_info": fetch_company_info,
}

TOOL_STATUS_MAP = {
    "rag_search": "searching_kb",
    "web_search": "researching",
    "generate_proposal": "writing_proposal",
    "generate_prd": "writing_prd",
    "fetch_company_info": "fetching_company_info",
}

# Tools that produce artifacts (return JSON with artifact_url)
ARTIFACT_TOOLS = {"generate_prd", "generate_proposal"}


class NameExtraction(BaseModel):
    name: str | None = Field(default=None, description="The user's name if provided.")


def _latest_ai_message(messages: list[BaseMessage]) -> AIMessage | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None


def _extract_user_name(text: str) -> str | None:
    extractor = get_chat_model().with_structured_output(
        NameExtraction, method="json_schema"
    )
    result = extractor.invoke(
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


def agent_node(state: AgentState) -> dict[str, Any]:
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
            extracted_name = _extract_user_name(
                str(getattr(latest_human, "content", ""))
            )
            if extracted_name:
                user_name = extracted_name

    llm = get_chat_model().bind_tools(list(TOOL_MAP.values()))
    prompt = build_agent_system_prompt(user_name)
    response = llm.invoke(
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


def tools_node(state: AgentState) -> dict[str, Any]:
    messages = list(state.get("messages", []))
    last_ai = _latest_ai_message(messages)
    tool_calls = list(getattr(last_ai, "tool_calls", []) or [])

    tool_messages: list[ToolMessage] = []
    new_artifact_urls: list[str] = []
    latest_artifact_url: str | None = None

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

        logger.info(f"Tool Call: {tool_name} with args: {tool_args}")
        try:
            result = tool_fn.invoke(tool_args)
            
            # Truncate result for logging if it's a long string
            log_result = result
            if isinstance(result, str) and len(result) > 500:
                log_result = result[:500] + "... [truncated]"
            
            logger.info(f"Tool Response: {tool_name} result: {log_result}")
        except Exception as exc:  # pragma: no cover
            logger.error(f"Tool Error: {tool_name} error: {exc}", exc_info=True)
            result = f"Tool error: {exc}"

        # For artifact tools: parse the JSON, extract URL, pass clean message to agent
        tool_message_content = result
        if tool_name in ARTIFACT_TOOLS and isinstance(result, str):
            try:
                parsed = json.loads(result)
                artifact_url = parsed.get("artifact_url")
                if artifact_url:
                    new_artifact_urls.append(artifact_url)
                    latest_artifact_url = artifact_url
                # Agent only sees the clean message, not the JSON
                tool_message_content = parsed.get("message", result)
            except (json.JSONDecodeError, AttributeError):
                pass  # Not JSON, pass as-is

        tool_messages.append(
            ToolMessage(
                content=tool_message_content,
                tool_call_id=tool_call.get("id", tool_name),
            )
        )

    output: dict[str, Any] = {"messages": tool_messages, "agent_status": "idle"}

    if new_artifact_urls:
        output["artifacts"] = new_artifact_urls  # appended via operator.add
    if latest_artifact_url:
        output["current_artifact"] = latest_artifact_url  # overwritten (last wins)

    return output
