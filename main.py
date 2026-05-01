from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

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


def _print_banner(session_id: str) -> None:
    print("nom-chatbot CLI")
    print(f"session: {session_id}")
    print("commands: /history, /new, /exit, /quit")
    print()


def _print_history(messages: list[BaseMessage]) -> None:
    if not messages:
        print("No messages yet.")
        return

    for message in messages:
        role = "BOT" if isinstance(message, AIMessage) else "YOU"
        print(f"{role}: {_message_text(message)}")


async def _stream_turn(
    graph: Any,
    turn_input: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    latest_state: dict[str, Any] = {}
    current_status: str | None = "idle"

    async for state in graph.astream(turn_input, config=config, stream_mode="values"):
        latest_state = dict(state or {})
        next_status = latest_state.get("agent_status")
        if next_status and next_status != current_status:
            print(f"STATUS: {next_status}")
            current_status = next_status

    if current_status != "idle":
        print("STATUS: idle")

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

            _print_banner(active_session_id)

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
                    print(f"new session: {active_session_id}")
                    continue

                if command == "/history":
                    snapshot = await graph.aget_state(config)
                    messages = list((snapshot.values or {}).get("messages", []))
                    _print_history(messages)
                    continue

                turn_input: dict[str, Any] = {
                    "messages": [HumanMessage(content=user_input)],
                    "session_id": active_session_id,
                    "agent_status": "idle",
                }
                result = await _stream_turn(graph, turn_input, config)
                messages = list(result.get("messages", []))
                last_ai = _find_last_ai_message(messages)
                print(f"BOT: {_message_text(last_ai) if last_ai else ''}")
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
