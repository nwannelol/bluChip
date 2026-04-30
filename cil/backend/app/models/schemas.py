"""Pydantic schemas for all API request/response bodies."""

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1)
    channel: Literal["web", "whatsapp"] = "web"


class Source(BaseModel):
    content: str
    metadata: dict


class ChatResponse(BaseModel):
    session_id: str
    agent: str
    response: str
    sources: list[Source] = []
    is_stub: bool = False


class AgentStatusCard(BaseModel):
    name: str
    label: str
    active: bool
    is_stub: bool
    description: str


class AdminOverviewResponse(BaseModel):
    agents: list[AgentStatusCard]
    total_conversations: int
    total_messages: int
