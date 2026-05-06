"""Pydantic request / response schemas for NEXUS API endpoints."""

import uuid
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent: Literal["fan", "media", "scout", "ops"] = "fan"
    channel: Literal["web", "whatsapp"] = "web"


class Source(BaseModel):
    content: str
    metadata: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    session_id: str
    agent: str
    response: str
    sources: list[Source] = []
    is_stub: bool = False


# ── Admin schemas ─────────────────────────────────────────────────────────────

class AgentInfo(BaseModel):
    name: str
    display_name: str
    description: str
    status: Literal["active", "stub"]
    is_stub: bool


class AgentLogEntry(BaseModel):
    id: str
    agent_name: str
    session_id: str
    action: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: str


class KnowledgeRefreshResponse(BaseModel):
    status: str
    message: str
