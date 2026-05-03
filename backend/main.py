from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver

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
    console.print("[bold green]NOM CHAT CLI[/]")
    console.print(f"session: [cyan]{session_id}[/]")
    console.print(
        "commands: [yellow]/history[/], [yellow]/new[/], [yellow]/quit[/]"
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
    # Run the graph synchronously in a thread pool to avoid async DB overhead/errors
    loop = asyncio.get_running_loop()
    final_state = await loop.run_in_executor(
        None, 
        lambda: graph.invoke(turn_input, config=config)
    )

    # Extract the last AI message
    messages = final_state.get("messages", [])
    last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
    
    if not last_ai:
        console.print("[bold red]Error: No response from agent.[/]")
        return final_state

    # 1. Print Tool Calls
    if hasattr(last_ai, "tool_calls") and last_ai.tool_calls:
        console.print("[bold yellow]Tool Calls:[/]")
        for call in last_ai.tool_calls:
            console.print(Panel(json.dumps(call.get("args"), indent=2), title=f"TOOL: {call.get('name')}"))

    # 2. Print Tool Responses
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            console.print(Panel(Markdown(msg.content), title=f"Response: {msg.tool_call_id}"))
        if isinstance(msg, AIMessage) and msg == last_ai:
            break # Only get tools for the CURRENT turn

    # 3. Stream the text content (simulated)
    console.print(Rule())
    content = _chunk_text(last_ai)
    assistant_text = Text()
    panel = Panel(assistant_text, title="STATUS: idle")
    
    with Live(panel, console=console, refresh_per_second=10) as live:
        chunk_size = 4
        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]
            assistant_text.append(chunk)
            live.update(Panel(assistant_text, title="STATUS: idle"))
            await asyncio.sleep(0.01)

    console.print(Rule())
    return final_state


async def _read_input(prompt: str) -> str:
    return await asyncio.to_thread(input, prompt)


async def run_cli(session_id: str | None = None) -> None:
    settings = get_settings()
    active_session_id = session_id or uuid4().hex

    try:
        graph = build_graph()
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
    asyncio.run(run_cli(session_id=args.session_id))
