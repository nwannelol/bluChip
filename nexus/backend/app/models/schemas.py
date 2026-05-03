"""Pydantic request / response schemas for NEXUS API endpoints."""

import uuid
from typing import Literal

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
