from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_core.tools import tool

DEFAULT_HOURLY_RATE = 150


@dataclass(frozen=True)
class CostEstimate:
    hours_low: int
    hours_high: int
    hourly_rate: int = DEFAULT_HOURLY_RATE

    @property
    def total_low(self) -> int:
        return self.hours_low * self.hourly_rate

    @property
    def total_high(self) -> int:
        return self.hours_high * self.hourly_rate


def estimate_project_cost(requirements: str) -> CostEstimate:
    text = requirements.lower()
    complexity = 0

    keyword_weights = {
        "auth": 6,
        "login": 6,
        "payment": 8,
        "dashboard": 5,
        "admin": 4,
        "api": 6,
        "integration": 7,
        "analytics": 5,
        "mobile": 8,
        "workflow": 5,
        "ai": 8,
        "search": 4,
        "rag": 7,
        "multi-tenant": 8,
    }

    for keyword, weight in keyword_weights.items():
        if keyword in text:
            complexity += weight

    size_bonus = 0
    if len(re.findall(r"\w+", text)) > 180:
        size_bonus += 8
    if len(re.findall(r"\w+", text)) > 350:
        size_bonus += 8

    total_complexity = complexity + size_bonus
    if total_complexity <= 10:
        return CostEstimate(40, 70)
    if total_complexity <= 22:
        return CostEstimate(70, 120)
    if total_complexity <= 36:
        return CostEstimate(120, 180)
    return CostEstimate(180, 280)


@tool
def estimate_cost(requirements: str) -> str:
    """Estimate delivery effort and cost from a project brief."""

    estimate = estimate_project_cost(requirements)
    return (
        "Estimated delivery range:\n"
        f"- Effort: {estimate.hours_low}-{estimate.hours_high} hours\n"
        f"- Rate: ${estimate.hourly_rate}/hour\n"
        f"- Cost: ${estimate.total_low:,}-${estimate.total_high:,}\n"
        "\nAssumptions:\n"
        "- Scope is a first production release.\n"
        "- No unusual vendor procurement or compliance work is included."
    )
