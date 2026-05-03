# PRD Tool Implementation — How Status Updates Work

## The Core Idea

The `generate_prd` tool itself is **pure logic** — it doesn't touch state.
Status is managed by inserting a thin `set_tool_status` node **before** the
tools node in the graph. Since LangGraph checkpoints state after every node,
the status update hits the SSE stream *before* the slow tool starts running.

```
[agent_node]  →  [set_tool_status]  →  [tools_node]  →  [agent_node]
    ↑                    ↓                   ↓
 "thinking"        "writing_prd"          "idle"
                  ← emitted here,
                    before tool runs
```

---

## File 1 — `state.py`

```python
from typing import Literal
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    user_name: str | None = None
    agent_status: Literal[
        "idle",
        "thinking",
        "researching",
        "writing_proposal",
        "writing_prd",
    ] = "idle"
```

---

## File 2 — `tools/prd.py`

Pure generation logic. No state, no status — just build the PRD.

```python
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

PRD_SYSTEM_PROMPT = """
You are a senior product manager. Given a project brief, write a detailed PRD
with the following sections:

1. **Overview** — One-paragraph summary
2. **Goals & Non-Goals** — Bullet list
3. **User Stories** — Formatted as "As a [role], I want [X] so that [Y]"
4. **Functional Requirements** — Numbered list, grouped by feature area
5. **Non-Functional Requirements** — Performance, security, scalability
6. **Out of Scope** — Explicit exclusions
7. **Open Questions** — Unresolved decisions
"""

@tool
def generate_prd(requirements: str, research: str) -> str:
    """
    Generate a detailed PRD from a project brief.

    Args:
        requirements: Plain-English description of what needs to be built,
                      including goals, users, and any known constraints.
    Returns:
        A structured PRD as a markdown string.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

    messages = [
        {"role": "system", "content": PRD_SYSTEM_PROMPT},
        {"role": "user",   "content": f"Project Brief:\n\n{requirements}\n---\nResearch on Topic:\n\n{research}"},
    ]

    response = llm.invoke(messages)
    return response.content
```

---

## File 3 — `nodes/tools_node.py` ← THE KEY FILE

```python
from langchain_core.messages import ToolMessage
from state import AgentState
from tools.prd import generate_prd
from tools.rag import rag_search
from tools.proposal import generate_proposal
from tools.estimate import estimate_cost

# Maps tool name → status shown to user while it runs
TOOL_STATUS_MAP = {
    "generate_prd":      "writing_prd",
    "generate_proposal": "writing_proposal",
    "rag_search":        "researching",
    "estimate_cost":     "thinking",
}

TOOLS = {
    "generate_prd":      generate_prd,
    "generate_proposal": generate_proposal,
    "rag_search":        rag_search,
    "estimate_cost":     estimate_cost,
}

def set_tool_status(state: AgentState) -> dict:
    """
    Runs BEFORE tools_node. Sets agent_status based on which tool is about
    to run. Because LangGraph checkpoints after every node, this status
    reaches the SSE stream before the slow tool starts.
    """
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"agent_status": "thinking"}

    first_tool_name = last_message.tool_calls[0]["name"]
    status = TOOL_STATUS_MAP.get(first_tool_name, "thinking")

    return {"agent_status": status}

def tools_node(state: AgentState) -> dict:
    """
    Executes tool calls from the last AIMessage.
    Resets agent_status to "idle" when done.
    """
    last_message  = state["messages"][-1]
    tool_calls    = last_message.tool_calls
    tool_messages = []

    for call in tool_calls:
        tool_fn = TOOLS.get(call["name"])

        if tool_fn is None:
            tool_messages.append(ToolMessage(
                content=f"Unknown tool: {call['name']}",
                tool_call_id=call["id"],
            ))
            continue

        try:
            result = tool_fn.invoke(call["args"])
            tool_messages.append(ToolMessage(
                content=result,
                tool_call_id=call["id"],
            ))
        except Exception as e:
            tool_messages.append(ToolMessage(
                content=f"Tool error: {str(e)}",
                tool_call_id=call["id"],
            ))

    return {
        "messages":     tool_messages,
        "agent_status": "idle",   # ← reset after tool finishes
    }
```

---

## File 4 — `graph.py`

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from state import AgentState
from nodes.tools_node import tools_node, set_tool_status
from tools.prd import generate_prd
from tools.rag import rag_search
from tools.proposal import generate_proposal
from tools.estimate import estimate_cost

TOOLS = [generate_prd, generate_proposal, rag_search, estimate_cost]
llm   = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(TOOLS)

def agent_node(state: AgentState) -> dict:
    system = SystemMessage(content=f"""
You are the website assistant for Newton on Mars.

{'Ask the user for their name before anything else.' if not state.get('user_name') else f"The user's name is {state['user_name']}. Address them by name."}

Use generate_prd for PRD requests and generate_proposal for proposal requests.
Do not write these as plain messages.
""")

    response = llm.invoke([system] + state["messages"])

    # Simple name capture heuristic (replace with LLM extraction in production)
    user_name = state.get("user_name")
    if not user_name:
        last_human = next(
            (m for m in reversed(state["messages"]) if m.type == "human"), None
        )
        if last_human and len(last_human.content.split()) <= 3:
            user_name = last_human.content.strip()

    return {
        "messages":     [response],
        "agent_status": "thinking",
        "user_name":    user_name,
    }

def should_use_tools(state: AgentState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "set_status"
    return "end"

def build_graph(checkpointer):
    builder = StateGraph(AgentState)

    builder.add_node("agent",      agent_node)
    builder.add_node("set_status", set_tool_status)  # ← inserted between agent and tools
    builder.add_node("tools",      tools_node)

    builder.set_entry_point("agent")

    builder.add_conditional_edges(
        "agent",
        should_use_tools,
        {"set_status": "set_status", "end": END},
    )

    builder.add_edge("set_status", "tools")
    builder.add_edge("tools",      "agent")

    return builder.compile(checkpointer=checkpointer)
```

---

## File 5 — `api/chat.py` (SSE endpoint)

```python
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from graph import get_graph

app = FastAPI()

STATUS_MESSAGES = {
    "idle":             "Done",
    "thinking":         "Thinking...",
    "researching":      "Searching knowledge base...",
    "writing_prd":      "Writing your PRD...",
    "writing_proposal": "Writing your project proposal...",
}

@app.post("/chat/{session_id}")
async def chat(session_id: str, body: dict):
    graph    = await get_graph()
    config   = {"configurable": {"thread_id": session_id}}
    user_msg = HumanMessage(content=body["message"])

    async def event_stream():
        last_status = None

        async for event in graph.astream_events(
            {"messages": [user_msg]},
            config=config,
            version="v2",
        ):
            kind = event["event"]
            data = event.get("data", {})

            # Status change (from set_tool_status or tools_node)
            if kind == "on_chain_end" and event.get("name") in (
                "set_status", "tools", "agent"
            ):
                new_status = data.get("output", {}).get("agent_status")
                if new_status and new_status != last_status:
                    last_status = new_status
                    yield f"event: status\ndata: {json.dumps({'status': new_status, 'message': STATUS_MESSAGES[new_status]})}\n\n"

            # Token stream (agent's final reply)
            elif kind == "on_chat_model_stream":
                chunk = data.get("chunk")
                if chunk and chunk.content:
                    yield f"event: token\ndata: {json.dumps({'token': chunk.content})}\n\n"

        yield f"event: done\ndata: {json.dumps({'status': 'idle'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

---

## What the Frontend Receives

For the message: *"Write me a PRD for a checkout redesign"*

```
event: status
data: {"status": "thinking", "message": "Thinking..."}
         ↑ agent_node just ran, deciding what to do

event: status
data: {"status": "writing_prd", "message": "Writing your PRD..."}
         ↑ set_tool_status node ran — user sees this BEFORE the tool starts
         ↑ this is the slow part (5–15s). User isn't clueless anymore.

event: status
data: {"status": "idle", "message": "Done"}
         ↑ tools_node finished, PRD is in state

event: token
data: {"token": "Here is your PRD:\n\n"}
event: token
data: {"token": "## Overview\n..."}
         ↑ agent streams its reply presenting the PRD

event: done
data: {"status": "idle"}
```

---

## Why This Design

| Decision | Why |
|---|---|
| set_tool_status is a separate node | LangGraph only checkpoints between nodes. Putting status update inside tools_node would be too late — tool already running. |
| Tool has no state concern | Clean separation. Tool is testable in isolation. |
| Status reset happens in tools_node return | After all tool calls in the batch finish, one clean reset. |
| astream_events not astream | Gives per-node and per-token events. astream only gives full state snapshots. |