"""TypedDicts mirroring Supabase table row shapes."""

from typing import Any, TypedDict


class KnowledgeBaseRow(TypedDict):
    id: str
    content: str
    metadata: dict[str, Any]
    similarity: float


class ConversationRow(TypedDict):
    id: str
    session_id: str
    channel: str
    created_at: str
    updated_at: str


class MessageRow(TypedDict):
    id: str
    conversation_id: str
    role: str
    content: str
    agent: str
    sources: list[dict[str, Any]]
    created_at: str


class AgentLogRow(TypedDict):
    id: str
    agent_name: str
    session_id: str
    action: str
    input: dict[str, Any]
    output: dict[str, Any]
    duration_ms: int | None
    error: str | None
    created_at: str
