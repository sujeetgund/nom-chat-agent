from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
import json
import logging
import asyncio
import queue as queue_mod
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent.graph import build_graph
from config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_settings()

# Absolute path to artifacts directory
ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Build graph once at startup. The factory handles the checkpointer.
    app.state.graph = build_graph()
    yield
    logger.info("Shutting down NOM Chat API.")

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
    """Helper to serialize messages to JSON-friendly dicts compatible with the frontend."""
    content = getattr(message, "content", str(message))
    
    if isinstance(message, AIMessage):
        role = "assistant"
    elif isinstance(message, HumanMessage):
        role = "user"
    else:
        role = "assistant" # Fallback
    
    res = {
        "id": getattr(message, "id", f"msg-{id(message)}"),
        "role": role, 
        "content": content,
        "timestamp": datetime.now().isoformat() # Fallback timestamp
    }
        
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
        try:
            loop = asyncio.get_running_loop()
            q: queue_mod.Queue = queue_mod.Queue()
            
            # Run graph.stream() in a background thread, pushing chunks to the queue
            def run_stream():
                try:
                    for chunk in graph.stream(turn_input, config=config, stream_mode="updates"):
                        q.put(("chunk", chunk))
                except Exception as e:
                    q.put(("error", e))
                finally:
                    q.put(("done", None))
            
            # Fire the stream thread (non-blocking)
            loop.run_in_executor(None, run_stream)
            
            current_artifact: str | None = None
            
            # Pull from queue in real-time, yielding SSE events as nodes complete
            while True:
                try:
                    msg_type, data = await loop.run_in_executor(
                        None, lambda: q.get(timeout=1.0)
                    )
                except queue_mod.Empty:
                    # Keep-alive comment to prevent connection timeout
                    yield ": keepalive\n\n"
                    continue
                
                if msg_type == "done":
                    break
                elif msg_type == "error":
                    logger.error(f"Stream error: {data}", exc_info=True)
                    yield f"event: error\ndata: {json.dumps({'detail': str(data)})}\n\n"
                    break
                
                # Process graph chunk: {node_name: node_output_dict}
                chunk = data
                for node_name, node_data in chunk.items():
                    # 1. Status updates
                    if "agent_status" in node_data:
                        status = node_data["agent_status"]
                        yield f"event: status\ndata: {json.dumps({'status': status, 'node': node_name})}\n\n"
                    
                    # 2. Track current_artifact (only when set by tools_node)
                    if "current_artifact" in node_data and node_data["current_artifact"]:
                        current_artifact = node_data["current_artifact"]
                    
                    # 3. AI message content (only final response, not tool-calling messages)
                    if "messages" in node_data:
                        for msg in node_data["messages"]:
                            if isinstance(msg, AIMessage) and not getattr(msg, "tool_calls", None):
                                content = _chunk_text(msg)
                                if content:
                                    run_id = getattr(msg, "id", None) or f"run-{id(msg)}"
                                    # Stream text in small chunks for UI feel
                                    chunk_size = 8
                                    for i in range(0, len(content), chunk_size):
                                        text_chunk = content[i : i + chunk_size]
                                        yield f"event: message\ndata: {json.dumps({'text': text_chunk, 'run_id': run_id})}\n\n"
                                        await asyncio.sleep(0.01)
            
            # 4. After all chunks: if an artifact was generated, send it as a final event
            if current_artifact:
                yield f"event: artifact\ndata: {json.dumps({'url': current_artifact})}\n\n"
            
            # 5. Final idle status
            yield f"event: status\ndata: {json.dumps({'status': 'idle'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat execution: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/chat/{session_id}/history")
async def chat_history(session_id: str, request: Request):
    graph = request.app.state.graph
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        loop = asyncio.get_running_loop()
        snapshot = await loop.run_in_executor(
            None,
            lambda: graph.get_state(config)
        )
        
        state_values = snapshot.values or {}
        messages = list(state_values.get("messages", []))
        artifacts = list(state_values.get("artifacts", []))
        
        # Filter out ToolMessages for the UI; also skip AI messages that only have tool_calls
        ui_messages = []
        for m in messages:
            if isinstance(m, HumanMessage):
                ui_messages.append(serialize_message(m))
            elif isinstance(m, AIMessage):
                # Skip messages that are purely tool-call dispatches (no visible text)
                content = _chunk_text(m)
                has_tool_calls = bool(getattr(m, "tool_calls", None))
                if content.strip() or not has_tool_calls:
                    ui_messages.append(serialize_message(m))
        
        return {
            "session_id": session_id,
            "messages": ui_messages,
            "artifacts": artifacts,  # list of URL strings
        }
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        return {"session_id": session_id, "messages": [], "artifacts": []}


@app.get("/artifacts/{filename}")
async def get_artifact(filename: str):
    """Serve a generated artifact markdown file."""
    # Sanitize filename to prevent directory traversal
    safe_name = Path(filename).name
    filepath = ARTIFACTS_DIR / safe_name
    
    if not filepath.exists() or not filepath.is_file():
        return PlainTextResponse("Artifact not found", status_code=404)
    
    content = filepath.read_text(encoding="utf-8")
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")
