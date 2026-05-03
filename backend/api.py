from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any
import json
import logging
import sys
import asyncio
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from agent.graph import build_graph
from config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

settings = get_settings()

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
    
    if hasattr(message, "tool_calls"):
        res["toolCalls"] = message.tool_calls
        
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
                yield f"event: error\ndata: {json.dumps({'detail': 'No response from agent'})}\n\n"
                return

            # Use message ID as run_id to ensure the frontend creates a new message block
            run_id = getattr(last_ai, "id", None) or uuid4().hex

            # 1. Yield tool calls if any
            if hasattr(last_ai, "tool_calls") and last_ai.tool_calls:
                for call in last_ai.tool_calls:
                    yield f"event: tool_call\ndata: {json.dumps({'name': call.get('name'), 'args': call.get('args'), 'id': call.get('id'), 'run_id': run_id})}\n\n"

            # 2. Yield tool results from the state
            for msg in reversed(messages):
                if isinstance(msg, ToolMessage):
                    yield f"event: tool_result\ndata: {json.dumps({'tool_call_id': msg.tool_call_id, 'result': msg.content, 'run_id': run_id})}\n\n"
                if isinstance(msg, AIMessage) and msg == last_ai:
                    break # Only get tools for the CURRENT turn

            # 3. Stream the text content in chunks (simulated streaming)
            content = _chunk_text(last_ai)
            chunk_size = 8
            for i in range(0, len(content), chunk_size):
                chunk = content[i : i + chunk_size]
                yield f"event: message\ndata: {json.dumps({'text': chunk, 'run_id': run_id})}\n\n"
                await asyncio.sleep(0.01) # Simulated pacing

            # 4. Final status reset
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
        # Use synchronous get_state in a thread pool to match our checkpointer
        loop = asyncio.get_running_loop()
        snapshot = await loop.run_in_executor(
            None,
            lambda: graph.get_state(config)
        )
        
        messages = list((snapshot.values or {}).get("messages", []))
        
        # Filter out ToolMessages and SystemMessages for the UI
        ui_messages = [
            serialize_message(m) 
            for m in messages 
            if isinstance(m, (HumanMessage, AIMessage))
        ]
        
        return {"session_id": session_id, "messages": ui_messages}
    except Exception as e:
        logger.error(f"Error getting history: {e}", exc_info=True)
        return {"session_id": session_id, "messages": []}
