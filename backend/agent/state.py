from __future__ import annotations

import operator
from typing import Annotated, Literal

from langgraph.graph import MessagesState

AgentStatus = Literal[
    "idle",
    "thinking",
    "researching",
    "writing_proposal",
    "writing_prd",
    "searching_kb",
]


class AgentState(MessagesState, total=False):
    user_name: str | None
    agent_status: AgentStatus
    session_id: str
    artifacts: Annotated[list[str], operator.add]  # list of artifact URLs (accumulated)
    current_artifact: str | None  # latest artifact URL (reset each turn)
