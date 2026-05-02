# Chat Agent Architecture

## Overview

A conversational AI agent embedded on the website that can answer questions from
website content (RAG), conduct research, and generate structured documents like
Project Proposals and PRDs — complete with cost estimates.

---

## Core Features

| Feature | Description |
| --- | --- |
| Website Q&A | RAG over services, blogs, case studies, team info |
| Research | Deep-dive answers using website knowledge base |
| Project Proposal | Structured proposal with scope, timeline, cost estimate |
| PRD | Product requirements document generation |
| Persistent Sessions | Conversation memory across page reloads |
| Live Status | Frontend knows what the agent is currently doing |

---

## Stack

| Layer | Choice | Reason |
| --- | --- | --- |
| Agent Framework | LangGraph | Simple 2-node ReAct loop, built-in checkpointing |
| LLM | OpenAI GPT-4o / Groq | Tool calling support |
| Backend | FastAPI | SSE streaming, async |
| Vector Store | pgvector (Postgres) | Unified DB, no extra infra |
| Session Store | PostgresSaver (LangGraph) | Checkpointer on same Postgres instance |
| Streaming | SSE | Aligned with existing project architecture |

---

## LangGraph Architecture

### 2-Node Design

```
[START]
   │
   ▼
[Agent Node]  ◄───────────────────────┐ (Return Tool Response to Agent)
   │                                  │
   ├── has tool calls? ──YES──► [Tools Node]
   │                                  
   └── NO (final reply) ──► [END]
```

This is the standard ReAct pattern. Keep it exactly this simple.

---

## State Schema

```python
from typing import Literal
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    user_name: str | None          # Captured on first message, persisted
    agent_status: Literal[
        "idle",
        "thinking",
        "researching",
        "writing_proposal",
        "writing_prd"
    ]
    session_id: str                # Same as LangGraph thread_id
    ...
```

> **Why explicit state?** The checkpointer saves the full state on every step.
`user_name` is captured once and never asked again across sessions.
`agent_status` is streamed to the frontend so users see real-time activity.
> 

---

## Tools (Tools Node)

| Tool | Trigger | Sets Status To |
| --- | --- | --- |
| `rag_search` | Questions about services, blogs, case studies | `searching_kb` |
| `generate_proposal` | User requests a project proposal | `writing_proposal` |
| `generate_prd` | User requests a PRD | `writing_prd` |
| `research` | Agent finds a need to research a topic on web before replying  | `researching` |

> **Note on web search:** Out of scope for v1. All research is grounded in the
website's knowledge base only. Add a `web_search` tool in v2 if needed.
> 

### Tool Status Update Pattern

Each tool updates `agent_status` at entry via a shared utility:

```python
def update_status(state: AgentState, status: str) -> AgentState:
    return {**state, "agent_status": status}

@tool
def generate_prd(requirements: str) -> str:
    # Status is set by the agent node before invoking tools
    # via a pre-tool-call hook or within the tools node itself
    ...
```

---

## Session & User Name Flow

```
User sends first message
        │
        ▼
State: user_name = None?
        │
       YES ──► Agent asks: "Hi! What's your name?"
        │
       NO  ──► Normal conversation continues
        │
User replies with name
        │
        ▼
Agent extracts name, stores in state.user_name
PostgresSaver checkpoints it
        │
        ▼
All future messages: agent addresses user by name
```

**Implementation note:** Put this logic in the system prompt:

```
If user_name is None, your FIRST response must only ask the user for their name.
Once you have it, confirm it warmly and proceed. Always address them by name.
```

---

## SSE Streaming + Status Updates

FastAPI endpoint streams two types of events:

```
event: status
data: {"status": "writing_prd", "message": "Writing your PRD..."}

event: token
data: {"token": "## Project Requirements\n"}

event: done
data: {"status": "idle"}
```

Frontend subscribes to the SSE stream and:

- Renders tokens progressively (chat bubble builds in real time)
- Shows a contextual status badge: `"Researching..."` / `"Writing PRD..."` etc.

---

## Database Schema

```sql
-- LangGraph checkpointer handles this automatically
-- Tables: checkpoints, checkpoint_writes, checkpoint_migrations

-- Vector store for RAG
CREATE TABLE website_embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content     TEXT NOT NULL,
    metadata    JSONB,              -- source, type (blog/service/case_study), url
    embedding   vector(1536)        -- OpenAI text-embedding-3-small
);

CREATE INDEX ON website_embeddings
    USING ivfflat (embedding vector_cosine_ops);
```

---

## API Design

```
POST /chat/session          → Create new session, returns session_id (thread_id)
GET  /chat/{session_id}     → SSE stream: send message, receive streamed reply
GET  /chat/{session_id}/history  → Return full message history for UI restore
```

---

## Folder Structure

```
app/
├── agent/
│   ├── graph.py          # LangGraph graph definition (2 nodes)
│   ├── state.py          # AgentState schema
│   ├── tools/
│   │   ├── rag.py        # rag_search tool
│   │   ├── proposal.py   # generate_proposal tool
│   │   ├── prd.py        # generate_prd tool
│   │   └── estimate.py   # estimate_cost tool
│   └── prompts.py        # System prompt with user_name injection
├── api/
│   ├── chat.py           # FastAPI SSE endpoint
│   └── session.py        # Session creation
├── rag/
│   ├── embedder.py       # Embed and upsert website content
│   └── retriever.py      # pgvector similarity search
└── db/
    ├── postgres.py       # Async Postgres connection
    └── checkpointer.py   # PostgresSaver setup
```

---

## Build Phases

### Phase 1 — Core Agent (Week 1)

- [x]  LangGraph 2-node graph with `AgentState`
- [ ]  `rag_search` tool + pgvector setup
- [x]  `PostgresSaver` checkpointer
- [ ]  FastAPI SSE endpoint
- [x]  User name capture flow via system prompt

### Phase 2 — Document Generation (Week 2)

- [ ]  `generate_proposal` tool with structured output
- [ ]  `generate_prd` tool with structured output
- [ ]  `estimate_cost` tool (rule-based + LLM hybrid)
- [ ]  `agent_status` streaming to frontend

### Phase 3 — Content & Polish (Week 3)

- [ ]  Ingest all website content into pgvector
- [ ]  Metadata filtering (search only blogs, or only services, etc.)
- [ ]  Frontend status badge component
- [ ]  Session restore on page reload

---

## Key Design Decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Node count | 2 (Agent + Tools) | ReAct is sufficient; avoid over-engineering |
| Session key | LangGraph thread_id | Don't build a separate session table |
| User name storage | AgentState.user_name | Checkpointed automatically, no separate DB call |
| PRD/Proposal as tools | Yes | Enables status tracking; not free-form agent output |
| Web search | DuckDuckGo Search for now | Simply use DuckDuckGo Search tool from langchain |
| Streaming | SSE (not WebSocket) | Simpler, stateless, fits FastAPI well |