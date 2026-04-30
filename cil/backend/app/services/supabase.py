"""Supabase client service — all DB calls must go through here.

Uses the service_role key to bypass RLS for backend operations.
"""

import time
from typing import Any

from supabase import AsyncClient, acreate_client

from app.config import Settings

_client: AsyncClient | None = None


async def get_supabase(settings: Settings | None = None) -> AsyncClient:
    """Return (or lazily create) the Supabase async client singleton."""
    global _client
    if _client is None:
        cfg = settings or Settings()
        _client = await acreate_client(
            cfg.supabase_url.strip().strip("'"),
            cfg.supabase_service_role_key.strip().strip("'"),
        )
    return _client


# ---------------------------------------------------------------------------
# conversations
# ---------------------------------------------------------------------------

async def get_or_create_conversation(session_id: str, channel: str) -> str:
    """Return the conversation UUID for a session, creating it if needed."""
    db = await get_supabase()
    result = (
        await db.table("conversations")
        .select("id")
        .eq("session_id", session_id)
        .maybe_single()
        .execute()
    )
    if result.data:
        return result.data["id"]

    insert = (
        await db.table("conversations")
        .insert({"session_id": session_id, "channel": channel})
        .execute()
    )
    return insert.data[0]["id"]


# ---------------------------------------------------------------------------
# messages
# ---------------------------------------------------------------------------

async def save_message(
    *,
    conversation_id: str,
    role: str,
    content: str,
    agent: str,
    sources: list[dict[str, Any]] | None = None,
) -> None:
    """Persist a single conversation turn."""
    db = await get_supabase()
    await db.table("messages").insert(
        {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "agent": agent,
            "sources": sources or [],
        }
    ).execute()


async def get_conversation_history(
    conversation_id: str, limit: int = 20
) -> list[dict[str, Any]]:
    """Return the last `limit` messages for a conversation, oldest first."""
    db = await get_supabase()
    result = (
        await db.table("messages")
        .select("role, content, agent, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return result.data or []


# ---------------------------------------------------------------------------
# agent_logs
# ---------------------------------------------------------------------------

async def log_agent_action(
    *,
    agent_name: str,
    session_id: str,
    action: str,
    input_data: dict[str, Any] | None = None,
    output_data: dict[str, Any] | None = None,
    duration_ms: int | None = None,
    error: str | None = None,
) -> None:
    """Append an immutable audit record to agent_logs."""
    db = await get_supabase()
    await db.table("agent_logs").insert(
        {
            "agent_name": agent_name,
            "session_id": session_id,
            "action": action,
            "input": input_data or {},
            "output": output_data or {},
            "duration_ms": duration_ms,
            "error": error,
        }
    ).execute()


# ---------------------------------------------------------------------------
# knowledge_base (RAG)
# ---------------------------------------------------------------------------

async def similarity_search(
    query_embedding: list[float],
    match_threshold: float = 0.5,
    match_count: int = 5,
) -> list[dict[str, Any]]:
    """Run the pgvector cosine similarity RPC defined in migration 001."""
    db = await get_supabase()
    result = await db.rpc(
        "match_knowledge_base",
        {
            "query_embedding": query_embedding,
            "match_threshold": match_threshold,
            "match_count": match_count,
        },
    ).execute()
    return result.data or []


async def insert_knowledge_chunk(
    content: str,
    embedding: list[float],
    metadata: dict[str, Any] | None = None,
) -> str:
    """Insert a document chunk into the knowledge base. Returns the new row id."""
    db = await get_supabase()
    result = (
        await db.table("knowledge_base")
        .insert({"content": content, "embedding": embedding, "metadata": metadata or {}})
        .execute()
    )
    return result.data[0]["id"]
