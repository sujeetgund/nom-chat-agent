# NOM Chatbot CLI

This repository now runs the chat agent as an async terminal app instead of a web API.
The agent keeps the original LangGraph structure, tool routing, and persisted session state.

## What It Does

- Answers questions using the local knowledge base in `docs/` and the repo README.
- Generates project proposals and PRDs through dedicated tools.
- Persists each conversation with LangGraph checkpointing.
- Lets the agent learn the user's name from the conversation itself.
- Shows live agent status changes while the graph runs.

## Requirements

- Python 3.12
- A running Postgres database that matches `DATABASE_URL`
- An OpenAI API key in `OPENAI_API_KEY`

`config.py` loads settings from `.env` and falls back to these defaults:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/nom`
- `OPENAI_LLM_MODEL=gpt-5.4-nano`

## Run It

Install or refresh dependencies with `uv`:

```bash
uv sync
```

Start the CLI:

```bash
uv run python main.py
```

Resume a specific session thread if you already know the session id:

```bash
uv run python main.py --session-id <thread-id>
```

## CLI Commands

Inside the chat loop, use these commands:

- `/history` prints the conversation stored in the current thread.
- `/new` starts a fresh session with a new thread id.
- `/exit` or `/quit` leaves the CLI.

Any other input is treated as a normal chat message and is echoed as `YOU:`.
Agent responses are printed as `BOT:`. Status updates appear as `STATUS:` lines
while the graph executes.

## Architecture

The implementation keeps the agent intentionally small:

- `agent/graph.py` builds the LangGraph and checkpointer-backed runtime.
- `agent/nodes.py` contains the agent node, tool-status node, and tool execution node.
- `agent/tools/` contains async tools for knowledge-base search, research, proposal generation, PRD generation, estimation, and email drafting.
- `main.py` provides the async REPL and command handling.

The graph uses a persisted `thread_id` as the session key, so the same session can be resumed across launches as long as the Postgres checkpointer is available.

## Notes

- The local knowledge-base search currently scans the repo markdown and Python files. It is a lightweight stand-in for a future vector store.
- There is no HTTP API yet; the CLI is the primary interface for now.
