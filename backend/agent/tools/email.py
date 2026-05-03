"""Email drafting helper for future automation work."""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def draft_email(recipient: str, subject: str, body: str) -> str:
    """Format an email draft for review."""

    return f"To: {recipient}\nSubject: {subject}\n\n{body}"
