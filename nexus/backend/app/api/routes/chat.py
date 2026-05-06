"""Chat API endpoint.

POST /api/v1/chat        — route a message through the NEXUS orchestrator.
POST /api/v1/chat/stream — stream the Fan Agent response via SSE.
"""

import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.agents.fan.agent import FanAgent
from app.agents.scout.agent import ScoutAgent
from app.config import Settings
from app.dependencies import get_graph, get_settings
from app.models.schemas import ChatRequest, ChatResponse, Source
from app.services.supabase import fetch_conversation_history

logger = logging.getLogger("nexus.api.chat")

router = APIRouter()

_LIVE_AGENTS = {"fan", "scout"}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    """Route a message through the NEXUS orchestrator and return the response."""
    graph = get_graph()

    history = await fetch_conversation_history(request.session_id, settings, limit=10)

    state = {
        "message": request.message,
        "channel": request.channel,
        "session_id": request.session_id,
        "target_agent": request.agent,
        "conversation_history": history,
        "retrieved_docs": [],
        "agent_response": "",
        "sources": [],
        "error": None,
    }

    try:
        result = await graph.ainvoke(state)
    except Exception as exc:
        logger.exception("Orchestrator error for session %s", request.session_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result.get("error"):
        raise HTTPException(status_code=500, detail=result["error"])

    sources = [Source(**s) for s in result.get("sources", [])]

    return ChatResponse(
        session_id=request.session_id,
        agent=request.agent,
        response=result["agent_response"],
        sources=sources,
        is_stub=request.agent not in _LIVE_AGENTS,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Stream a Fan Agent response token-by-token via SSE.

    Event format:  data: <token>\\n\\n
    Terminal event: data: [DONE]\\n\\n

    Non-fan agents fall back to a single-chunk stream.
    """
    history = await fetch_conversation_history(request.session_id, settings, limit=10)
    base_state = {
        "message": request.message,
        "channel": request.channel,
        "session_id": request.session_id,
        "conversation_history": history,
    }

    async def _stream_fan() -> AsyncGenerator[str, None]:
        fan = FanAgent(settings)
        async for token in fan.stream(base_state):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    async def _stream_scout() -> AsyncGenerator[str, None]:
        scout = ScoutAgent(settings)
        async for token in scout.stream(base_state):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    async def _stream_graph() -> AsyncGenerator[str, None]:
        graph = get_graph()
        full_state = {
            **base_state,
            "target_agent": request.agent,
            "retrieved_docs": [],
            "agent_response": "",
            "sources": [],
            "error": None,
        }
        try:
            result = await graph.ainvoke(full_state)
            text = result.get("agent_response", "")
        except Exception as exc:
            logger.exception("Orchestrator error in stream for session %s", request.session_id)
            text = "An error occurred. Please try again."
        yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    if request.agent == "fan":
        gen = _stream_fan()
    elif request.agent == "scout":
        gen = _stream_scout()
    else:
        gen = _stream_graph()
    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
