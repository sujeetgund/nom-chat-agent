"""Project proposal generation tool."""

from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from .common import get_chat_model
from .prd import _generate_cost_estimate, _create_artifact

PROPOSAL_SYSTEM_PROMPT = """
You are a senior solutions consultant.
Write a proposal that includes:

1. Executive Summary
2. Problem Statement
3. Proposed Solution
4. Scope and Deliverables
5. Timeline
6. Assumptions and Constraints
7. Team / Delivery Approach
8. Risks and Mitigation
9. Next Steps

Keep it practical, concise, and specific to the project brief.
Do NOT include a cost estimate section; it will be added separately.
""".strip()


@tool
async def generate_proposal(requirements: str, research: str = "") -> str:
    """Generate a structured project proposal as a markdown artifact (saved to artifacts/).

    Args:
        requirements: Project brief and requirements
        research: Supporting research notes (auto-gathered if not provided)

    Returns:
        Status message with artifact path (e.g., "✓ Proposal created: artifacts/PROPOSAL_2026-05-02_project.md")
    """
    llm = get_chat_model()

    # Generate proposal content
    response = await llm.ainvoke(
        [
            SystemMessage(content=PROPOSAL_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Project brief:\n\n"
                    f"{requirements}\n\n"
                    + (
                        f"Supporting research and context:\n\n{research}"
                        if research
                        else ""
                    )
                )
            ),
        ]
    )

    proposal_content = response.content
    cost_estimate = _generate_cost_estimate(requirements, "proposal")
    full_content = proposal_content + "\n" + cost_estimate

    # Extract project name from requirements
    project_name = requirements.split("\n")[0][:40] or "project"

    # Write artifact
    filepath, rel_path = await asyncio.to_thread(
        _create_artifact, full_content, project_name, "proposal"
    )

    return f"✓ Proposal created: {rel_path}\n\nRetrieve this file to review the full proposal."
