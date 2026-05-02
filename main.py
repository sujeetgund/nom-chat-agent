from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.rule import Rule
import json

from agent.graph import build_graph
from config import get_settings


def _message_text(message: BaseMessage) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


def _find_last_ai_message(messages: list[BaseMessage]) -> AIMessage | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message
    return None


def _chunk_text(chunk: Any) -> str:
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


def _print_banner(session_id: str, console: Console) -> None:
    console.print("[bold green]nom-chatbot CLI[/]")
    console.print(f"session: [cyan]{session_id}[/]")
    console.print(
        "commands: [yellow]/history[/], [yellow]/new[/], [yellow]/exit[/], [yellow]/quit[/]"
    )
    console.print()


def _print_history(messages: list[BaseMessage], console: Console) -> None:
    if not messages:
        console.print("No messages yet.")
        return

    for message in messages:
        role = "BOT" if isinstance(message, AIMessage) else "YOU"
        console.print(f"[bold]{role}:[/] {_message_text(message)}")


async def _stream_turn(
    graph: Any,
    turn_input: dict[str, Any],
    config: dict[str, Any],
    console: Console,
) -> dict[str, Any]:
    latest_state: dict[str, Any] = {}
    current_status: str | None = "idle"

    assistant_text = Text()
    status = "idle"

    panel = Panel(assistant_text, title=f"STATUS: {status}")

    with Live(panel, console=console, refresh_per_second=10) as live:
        final_ai_text: str | None = None
        final_tool_calls: list[tuple[str, Any]] = []
        final_tool_responses: list[tuple[str, Any]] = []
        seen_tool_call_ids: set[str] = set()
        seen_tool_response_ids: set[str] = set()

        async for event in graph.astream_events(
            turn_input, config=config, version="v2"
        ):
            event_name = event.get("event")
            event_data = event.get("data") or {}

            # Streamed text chunks from the chat model or chain
            if event_name in ("on_chat_model_stream", "on_chain_stream"):
                chunk = event_data.get("chunk")
                text = _chunk_text(chunk)
                if text:
                    assistant_text.append(text)
                    live.update(Panel(assistant_text, title=f"STATUS: {status}"))

            # End of chain/tool: capture final state and any tool call summaries
            if event_name in {"on_chain_end", "on_tool_end"}:
                output = event_data.get("output")
                if isinstance(output, dict):
                    latest_state = dict(output or {})
                    # collect final AI message text if present
                    messages = latest_state.get("messages") or []
                    last_ai = None
                    for m in messages:
                        if isinstance(m, AIMessage):
                            last_ai = m
                            if getattr(m, "tool_calls", None):
                                for call in m.tool_calls:
                                    call_id = call.get("id", "")
                                    if call_id and call_id not in seen_tool_call_ids:
                                        seen_tool_call_ids.add(call_id)
                                        final_tool_calls.append(
                                            (call.get("name", ""), call.get("args", {}))
                                        )

                        # tool response messages can appear as ToolMessage-like dicts or objects
                        if isinstance(m, dict) and m.get("tool_call_id"):
                            tool_id = m.get("tool_call_id")
                            if tool_id not in seen_tool_response_ids:
                                seen_tool_response_ids.add(tool_id)
                                final_tool_responses.append((tool_id, m.get("content")))
                        elif hasattr(m, "tool_call_id") and getattr(m, "tool_call_id"):
                            tool_id = getattr(m, "tool_call_id")
                            if tool_id not in seen_tool_response_ids:
                                seen_tool_response_ids.add(tool_id)
                                final_tool_responses.append(
                                    (tool_id, getattr(m, "content"))
                                )

                    if last_ai:
                        final_ai_text = _message_text(last_ai)

                    next_status = latest_state.get("agent_status")
                    if next_status and next_status != current_status:
                        status = next_status
                        current_status = next_status
                        live.update(Panel(assistant_text, title=f"STATUS: {status}"))

    # After streaming finishes, print status, tool-calls, tool-responses, then final AI message
    console.print(Rule())

    # Print last agent status (if any)
    if current_status:
        console.print(f"[green]STATUS:[/] {current_status}")

    # Helper to pretty-print/truncate args
    def _pretty_args(obj: Any, max_len: int = 400) -> str:
        try:

            def _truncate(item):
                if isinstance(item, str) and len(item) > max_len:
                    return item[:max_len] + "…"
                if isinstance(item, dict):
                    return {k: _truncate(v) for k, v in item.items()}
                if isinstance(item, list):
                    return [_truncate(x) for x in item]
                return item

            truncated = _truncate(obj)
            return json.dumps(truncated, indent=2, ensure_ascii=False)
        except Exception:
            return str(obj)

    # Tool calls
    if final_tool_calls:
        console.print("[bold yellow]Tool Calls:[/]")
        for name, args in final_tool_calls:
            pretty = _pretty_args(args)
            syntax = Syntax(pretty, "json", theme="monokai", word_wrap=True)
            console.print(Panel(syntax, title=f"TOOL: {name}"))

    # Tool responses
    if final_tool_responses:
        console.print("[bold cyan]Tool Responses:[/]")
        for call_id, content in final_tool_responses:
            if isinstance(content, str):
                console.print(Panel(Markdown(content), title=f"Response: {call_id}"))
            else:
                pretty = _pretty_args(content)
                syntax = Syntax(pretty, "json", theme="monokai", word_wrap=True)
                console.print(Panel(syntax, title=f"Response: {call_id}"))

    # Final assistant message
    if final_ai_text:
        console.print(Markdown(final_ai_text))

    # Close turn with idle status indicator
    if current_status != "idle":
        console.print(f"[green]STATUS:[/] idle")
    console.print(Rule())

    return latest_state


async def _read_input(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)


async def run_cli(session_id: str | None = None) -> None:
    settings = get_settings()
    active_session_id = session_id or uuid4().hex

    try:
        async with AsyncPostgresSaver.from_conn_string(
            settings.database_url
        ) as checkpointer:
            await checkpointer.setup()
            graph = build_graph(checkpointer)
            config = {"configurable": {"thread_id": active_session_id}}

            console = Console()
            _print_banner(active_session_id, console)

            while True:
                try:
                    user_input = (await _read_input("YOU: ")).strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break

                if not user_input:
                    continue

                command = user_input.lower()
                if command in {"/exit", "/quit"}:
                    break

                if command == "/new":
                    active_session_id = uuid4().hex
                    config = {"configurable": {"thread_id": active_session_id}}
                    console.print(f"new session: {active_session_id}")
                    continue

                if command == "/history":
                    snapshot = await graph.aget_state(config)
                    messages = list((snapshot.values or {}).get("messages", []))
                    _print_history(messages, console)
                    continue

                turn_input: dict[str, Any] = {
                    "messages": [HumanMessage(content=user_input)],
                    "session_id": active_session_id,
                    "agent_status": "idle",
                }
                result = await _stream_turn(graph, turn_input, config, console)
                messages = list(result.get("messages", []))
    except Exception as exc:  # pragma: no cover - runtime guard for CLI startup
        print(f"Failed to start the chat agent: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the NOM chat agent in a terminal."
    )
    parser.add_argument("--session-id", help="Resume a specific session/thread id.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    # On Windows, the default ProactorEventLoop is incompatible with
    # some async Postgres drivers (psycopg). Use the SelectorEventLoop
    # policy when running on Windows to avoid "ProactorEventLoop" errors.
    if sys.platform == "win32":
        try:
            # WindowsSelectorEventLoopPolicy is available on recent Pythons
            from asyncio import WindowsSelectorEventLoopPolicy

            asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        except Exception:
            # Fallback: ignore if policy isn't available for some reason
            pass

    asyncio.run(run_cli(session_id=args.session_id))
