from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from ..prompts import PRD_SYSTEM_PROMPT
from .common import get_chat_model


def _generate_cost_estimate(requirements: str, project_type: str = "prd") -> str:
    """Generate a simple cost estimate section based on project requirements."""
    # Simple heuristic: count complexity keywords
    complex_keywords = ["ml", "ai", "agent", "rag", "llm", "realtime", "scale", "api"]
    complexity = sum(1 for kw in complex_keywords if kw.lower() in requirements.lower())

    # Base estimates
    if project_type == "prd":
        base_hours_low = 40
        base_hours_high = 80
    else:  # proposal
        base_hours_low = 80
        base_hours_high = 120

    hours_low = base_hours_low + (complexity * 20)
    hours_high = base_hours_high + (complexity * 30)
    hourly_rate = 150

    total_low = hours_low * hourly_rate
    total_high = hours_high * hourly_rate

    # Infrastructure estimate (rough)
    cloud_compute_low = 500  # monthly for small infra
    cloud_compute_high = 2000
    llm_inference_est = 1000  # monthly, variable

    return f"""
## Cost Estimate

**Development:**
- Estimated effort: {hours_low}-{hours_high} hours @ ${hourly_rate}/hour
- Subtotal: ${total_low:,} - ${total_high:,}

**Infrastructure (Monthly, after launch):**
- Cloud compute (AWS/GCP/Azure): ${cloud_compute_low:,} - ${cloud_compute_high:,}
- LLM inference and API calls: ~${llm_inference_est:,}
- Storage & bandwidth: ~$500-$1,500
- Total monthly (estimate): ${cloud_compute_low + llm_inference_est + 500:,} - ${cloud_compute_high + llm_inference_est + 1500:,}

*Note: Costs assume standard cloud pricing and OpenAI/similar LLM APIs. Actual costs vary by scale, traffic, and provider choice.*
"""


def _create_artifact(
    content: str, project_name: str = "project", doc_type: str = "prd"
) -> tuple[str, str]:
    """Write artifact to artifacts/ directory and return (filepath, relative_path)."""
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    project_slug = project_name.lower().replace(" ", "-")[:30]
    filename = f"{doc_type.upper()}_{timestamp}_{project_slug}.md"
    filepath = artifacts_dir / filename

    filepath.write_text(content, encoding="utf-8")
    return str(filepath), f"artifacts/{filename}"


@tool
def generate_prd(requirements: str, research: str = "") -> str:
    """Generate a structured PRD as a markdown artifact (saved to artifacts/).

    Args:
        requirements: Project brief and requirements
        research: Supporting research notes (auto-gathered if not provided)

    Returns:
        Status message with artifact path (e.g., "✓ PRD created: artifacts/PRD_2026-05-02_project.md")
    """
    llm = get_chat_model()

    # Generate PRD content
    response = llm.invoke(
        [
            SystemMessage(content=PRD_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    "Project brief:\n\n"
                    f"{requirements}\n\n"
                    + (f"Supporting research:\n\n{research}\n\n" if research else "")
                    + "\nInclude a detailed cost estimate section."
                )
            ),
        ]
    )

    prd_content = response.content
    cost_estimate = _generate_cost_estimate(requirements, "prd")
    full_content = prd_content + "\n" + cost_estimate

    # Extract project name from requirements (first line or first 30 chars)
    project_name = requirements.split("\n")[0][:40] or "project"

    # Write artifact
    filepath, rel_path = _create_artifact(full_content, project_name, "prd")

    return f"✓ PRD created: {rel_path}\n\nRetrieve this file to review the full PRD."
