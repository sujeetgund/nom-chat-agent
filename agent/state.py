from typing import Literal

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
