from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from ..prompts import PRD_SYSTEM_PROMPT
from .common import get_chat_model


@tool
async def generate_prd(requirements: str, research: str) -> str:
    """Generate a structured PRD from a project brief and supporting research."""

    llm = get_chat_model()
    response = await llm.ainvoke(
        [
            SystemMessage(content=PRD_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Project brief:\n\n"
                    f"{requirements}\n\n"
                    "Supporting research:\n\n"
                    f"{research}"
                )
            ),
        ]
    )
    return response.content
