from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from ..prompts import PRD_SYSTEM_PROMPT
from .common import get_chat_model

# Absolute path to artifacts directory (relative to backend root)
ARTIFACTS_DIR = Path(__file__).resolve().parents[2] / "artifacts"


def _create_artifact(
    content: str, project_name: str = "project", doc_type: str = "prd"
) -> tuple[str, str]:
    """Write artifact to artifacts/ directory and return (filepath, filename)."""
    ARTIFACTS_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    project_slug = project_name.lower().replace(" ", "-")[:30]
    filename = f"{doc_type.upper()}_{timestamp}_{project_slug}.md"
    filepath = ARTIFACTS_DIR / filename

    filepath.write_text(content, encoding="utf-8")
    return str(filepath), filename


@tool
def generate_prd(requirements: str, research: str = "") -> str:
    """Generate a structured PRD as a markdown artifact (saved to artifacts/).

    Args:
        requirements: Project brief and requirements
        research: Supporting research notes (auto-gathered if not provided)

    Returns:
        JSON with message and artifact_url for the generated PRD.
    """
    llm = get_chat_model()

    response = llm.invoke(
        [
            SystemMessage(content=PRD_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Project brief:\n\n"
                    f"{requirements}\n\n"
                    + (f"Supporting research:\n\n{research}\n\n" if research else "")
                    + "\nInclude a rough cost estimate section based on your knowledge of typical project costs."
                )
            ),
        ]
    )

    prd_content = response.content
    project_name = requirements.split("\n")[0][:40] or "project"
    filepath, filename = _create_artifact(prd_content, project_name, "prd")

    return json.dumps({
        "message": "PRD generated successfully.",
        "artifact_url": f"/artifacts/{filename}",
    })


@tool
def generate_proposal(requirements: str, research: str = "") -> str:
    """Generate a structured project proposal as a markdown artifact (saved to artifacts/).

    Args:
        requirements: Project brief and requirements
        research: Supporting research notes (auto-gathered if not provided)

    Returns:
        JSON with message and artifact_url for the generated proposal.
    """
    from .proposal import PROPOSAL_SYSTEM_PROMPT

    llm = get_chat_model()

    response = llm.invoke(
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
                    + "\nInclude a rough cost and timeline estimate based on your knowledge."
                )
            ),
        ]
    )

    proposal_content = response.content
    project_name = requirements.split("\n")[0][:40] or "project"
    filepath, filename = _create_artifact(proposal_content, project_name, "proposal")

    return json.dumps({
        "message": "Proposal generated successfully.",
        "artifact_url": f"/artifacts/{filename}",
    })
