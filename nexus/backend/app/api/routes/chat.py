"""Chat API endpoint.

POST /api/v1/chat — accepts a message and routes it through the
NEXUS LangGraph orchestrator, returning the agent's response.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_graph, get_settings
from app.config import Settings
from app.models.schemas import ChatRequest, ChatResponse, Source

logger = logging.getLogger("nexus.api.chat")

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
) -> ChatResponse:
    """Route a message through the NEXUS orchestrator and return the response."""
    graph = get_graph()

    state = {
        "message": request.message,
        "channel": request.channel,
        "session_id": request.session_id,
        "target_agent": request.agent,
        "conversation_history": [],
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
        is_stub=request.agent != "fan",
    )
