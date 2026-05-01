"""Project proposal generation tool."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from .common import get_chat_model
from .estimate import estimate_project_cost

PROPOSAL_SYSTEM_PROMPT = """
You are a senior solutions consultant.
Write a proposal that includes:

1. Executive Summary
2. Problem Statement
3. Proposed Solution
4. Scope
5. Assumptions
6. Timeline
7. Team / Delivery Approach
8. Cost Estimate
9. Risks and Open Questions

Keep it practical, concise, and specific to the project brief.
""".strip()


@tool
async def generate_proposal(requirements: str, research: str) -> str:
    """Generate a structured project proposal from a brief and research notes."""

    llm = get_chat_model()
    estimate = estimate_project_cost(requirements)
    response = await llm.ainvoke(
        [
            SystemMessage(content=PROPOSAL_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Project brief:\n\n"
                    f"{requirements}\n\n"
                    "Research notes:\n\n"
                    f"{research}\n\n"
                    "Cost estimate:\n\n"
                    f"{estimate.hours_low}-{estimate.hours_high} hours at ${estimate.hourly_rate}/hour"
                    f" (${estimate.total_low:,}-${estimate.total_high:,})."
                )
            ),
        ]
    )
    return response.content
