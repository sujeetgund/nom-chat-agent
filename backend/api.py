from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
import json
import logging
import sys
import asyncio

# On Windows, psycopg requires the SelectorEventLoop
if sys.platform == "win32":
    try:
        from asyncio import WindowsSelectorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage, AIMessage

from agent.graph import build_graph
from config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
    }
    async with AsyncConnectionPool(
        settings.database_url, 
        kwargs=connection_kwargs,
        min_size=1,
        max_size=10,
        max_idle=300,
    ) as pool:
        await pool.wait()
        checkpointer = AsyncPostgresSaver(pool)
        logger.info("Setting up the checkpoint db.")
        await checkpointer.setup()  # run only the first time
        
        # Store in app state
        app.state.checkpointer = checkpointer
        app.state.graph = build_graph(checkpointer)
        
        yield {"checkpointer": checkpointer}
        logger.info("Closing the connection pool.")

app = FastAPI(lifespan=lifespan, title="NOM Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

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

def serialize_message(message: Any) -> dict[str, Any]:
    """Helper to serialize messages to JSON-friendly dicts."""
    if hasattr(message, "to_json"):
        # Some LangChain messages have to_json
        try:
            data = message.to_json()
            if "kwargs" in data:
                return {
                    "type": data.get("id", [""])[-1].lower().replace("message", ""),
                    "content": data["kwargs"].get("content", ""),
                    "tool_calls": data["kwargs"].get("tool_calls", [])
                }
        except:
            pass

    if isinstance(message, dict):
        return message

    content = getattr(message, "content", str(message))
    if isinstance(message, AIMessage):
        type_str = "ai"
    elif isinstance(message, HumanMessage):
        type_str = "human"
    elif isinstance(message, ToolMessage):
        type_str = "tool"
    elif isinstance(message, SystemMessage):
        type_str = "system"
    else:
        type_str = "unknown"
    
    res = {"type": type_str, "content": content}
    if hasattr(message, "tool_calls"):
        res["tool_calls"] = message.tool_calls
    return res

@app.post("/chat/{session_id}")
async def chat_endpoint(session_id: str, payload: ChatRequest, request: Request):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": session_id}}
    
    turn_input = {
        "messages": [HumanMessage(content=payload.message)],
        "session_id": session_id,
        "agent_status": "idle",
    }
    
    async def event_generator():
        current_status = "idle"
        
        try:
            async for event in graph.astream_events(turn_input, config=config, version="v2"):
                event_name = event.get("event")
                event_data = event.get("data") or {}

                # Streamed text chunks from the chat model
                if event_name == "on_chat_model_stream":
                    chunk = event_data.get("chunk")
                    text = _chunk_text(chunk)
                    if text:
                        yield f"event: message\ndata: {json.dumps({'text': text, 'run_id': event.get('run_id')})}\n\n"

                # Detect when a model ends (handles non-streaming or final sync)
                if event_name == "on_chat_model_end":
                    output = event_data.get("output")
                    if isinstance(output, AIMessage):
                        # ...
                        if output.tool_calls:
                            for call in output.tool_calls:
                                yield f"event: tool_call\ndata: {json.dumps({'name': call.get('name'), 'args': call.get('args'), 'run_id': event.get('run_id')})}\n\n"

                # Capture state updates for status
                if event_name == "on_chain_stream":
                    # This yields the intermediate state chunks
                    if isinstance(event_data, dict) and "chunk" in event_data:
                        chunk = event_data["chunk"]
                        # LangGraph chunks are often dicts of node outputs
                        for node_output in chunk.values():
                            if isinstance(node_output, dict):
                                next_status = node_output.get("agent_status")
                                if next_status and next_status != current_status:
                                    current_status = next_status
                                    yield f"event: status\ndata: {json.dumps({'status': current_status})}\n\n"

                # Fallback for status updates at end of nodes
                if event_name in {"on_chain_end", "on_tool_end"}:
                    output = event_data.get("output")
                    if isinstance(output, dict):
                        next_status = output.get("agent_status")
                        if next_status and next_status != current_status:
                            current_status = next_status
                            yield f"event: status\ndata: {json.dumps({'status': current_status})}\n\n"
                                    
            # Reset status to idle when done
            yield f"event: status\ndata: {json.dumps({'status': 'idle'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat stream: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/chat/{session_id}/history")
async def chat_history(session_id: str, request: Request):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        snapshot = await graph.aget_state(config)
        messages = list((snapshot.values or {}).get("messages", []))
        
        serialized_messages = [serialize_message(m) for m in messages]
        return {"session_id": session_id, "messages": serialized_messages}
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        return {"session_id": session_id, "messages": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, loop="none")
