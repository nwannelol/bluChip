"""Supabase service wrapper.

All database calls go through this module — never call supabase directly
from agent or route files.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from supabase import Client, create_client

from app.config import Settings

logger = logging.getLogger("cil.supabase")


def _get_client(settings: Settings) -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


async def get_or_create_conversation(
    session_id: str,
    channel: str,
    settings: Settings,
) -> dict[str, Any]:
    """Fetch an existing conversation or create one for this session.

    Args:
        session_id: Unique identifier for the user session.
        channel: "web" or "whatsapp".
        settings: Injected application settings.

    Returns:
        The conversations row as a dict.
    """
    client = _get_client(settings)

    result = await asyncio.to_thread(
        lambda: client.table("conversations")
        .select("*")
        .eq("session_id", session_id)
        .maybe_single()
        .execute()
    )

    if result is not None and result.data:
        return result.data

    insert = await asyncio.to_thread(
        lambda: client.table("conversations")
        .insert({"session_id": session_id, "channel": channel})
        .execute()
    )
    return insert.data[0]


async def save_message(
    conversation_id: str,
    role: str,
    content: str,
    agent: str,
    sources: list[dict[str, Any]],
    settings: Settings,
) -> dict[str, Any]:
    """Append a message turn to a conversation.

    Args:
        conversation_id: UUID of the parent conversation row.
        role: "user" or "assistant".
        content: Message text.
        agent: "fan" | "media" | "scout" | "ops".
        sources: RAG citations (may be empty list).
        settings: Injected application settings.

    Returns:
        The inserted messages row as a dict.
    """
    client = _get_client(settings)
    result = await asyncio.to_thread(
        lambda: client.table("messages")
        .insert({
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "agent": agent,
            "sources": sources,
        })
        .execute()
    )
    return result.data[0]


async def log_agent_action(
    agent_name: str,
    session_id: str,
    action: str,
    input_data: dict[str, Any],
    output_data: dict[str, Any],
    settings: Settings,
    duration_ms: int | None = None,
    error: str | None = None,
) -> None:
    """Append an immutable audit entry to agent_logs.

    Args:
        agent_name: "fan" | "media" | "scout" | "ops".
        session_id: Session this action belongs to.
        action: Short label e.g. "rag_retrieve", "llm_call", "stub_response".
        input_data: Arbitrary input payload.
        output_data: Arbitrary output payload.
        settings: Injected application settings.
        duration_ms: How long the action took in milliseconds.
        error: Error message if the action failed.
    """
    client = _get_client(settings)
    try:
        await asyncio.to_thread(
            lambda: client.table("agent_logs")
            .insert({
                "agent_name": agent_name,
                "session_id": session_id,
                "action": action,
                "input": input_data,
                "output": output_data,
                "duration_ms": duration_ms,
                "error": error,
            })
            .execute()
        )
    except Exception as exc:
        logger.warning("Failed to write agent log: %s", exc)


async def fetch_agent_logs(
    settings: Settings,
    limit: int = 50,
    agent_name: str | None = None,
) -> list[dict[str, Any]]:
    """Return recent agent_logs rows, newest first.

    Args:
        settings: Injected application settings.
        limit: Max rows to return.
        agent_name: Optional filter — one of fan/media/scout/ops.
    """
    client = _get_client(settings)

    def _query() -> Any:
        q = (
            client.table("agent_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
        )
        if agent_name:
            q = q.eq("agent_name", agent_name)
        return q.execute()

    result = await asyncio.to_thread(_query)
    return result.data or []


async def fetch_conversation_history(
    session_id: str,
    settings: Settings,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return the most recent messages for a session, oldest first.

    Args:
        session_id: The session to fetch history for.
        settings: Injected application settings.
        limit: Maximum number of messages to return.

    Returns:
        List of messages rows ordered oldest → newest.
    """
    client = _get_client(settings)

    conv = await asyncio.to_thread(
        lambda: client.table("conversations")
        .select("id")
        .eq("session_id", session_id)
        .maybe_single()
        .execute()
    )

    if conv is None or not conv.data:
        return []

    result = await asyncio.to_thread(
        lambda: client.table("messages")
        .select("role, content, agent, created_at")
        .eq("conversation_id", conv.data["id"])
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    return list(reversed(result.data or []))


# ── Analytics ─────────────────────────────────────────────────────────────────

async def fetch_analytics_summary(settings: Settings) -> dict[str, Any]:
    """Aggregate fan engagement metrics in parallel."""
    client = _get_client(settings)
    today = datetime.now(timezone.utc).date().isoformat()

    total_convs, total_msgs, msgs_today, web_convs, wa_convs = await asyncio.gather(
        asyncio.to_thread(
            lambda: client.table("conversations").select("id", count="exact").execute()
        ),
        asyncio.to_thread(
            lambda: client.table("messages").select("id", count="exact").execute()
        ),
        asyncio.to_thread(
            lambda: client.table("messages")
            .select("id", count="exact")
            .gte("created_at", today)
            .execute()
        ),
        asyncio.to_thread(
            lambda: client.table("conversations")
            .select("id", count="exact")
            .eq("channel", "web")
            .execute()
        ),
        asyncio.to_thread(
            lambda: client.table("conversations")
            .select("id", count="exact")
            .eq("channel", "whatsapp")
            .execute()
        ),
    )

    return {
        "total_conversations": total_convs.count or 0,
        "total_messages": total_msgs.count or 0,
        "total_fans": total_convs.count or 0,
        "messages_today": msgs_today.count or 0,
        "channel_breakdown": {
            "web": web_convs.count or 0,
            "whatsapp": wa_convs.count or 0,
        },
    }


async def fetch_agent_stats(settings: Settings) -> dict[str, Any]:
    """Per-agent call count and average duration from agent_logs."""
    client = _get_client(settings)
    result = await asyncio.to_thread(
        lambda: client.table("agent_logs")
        .select("agent_name, duration_ms")
        .order("created_at", desc=True)
        .limit(1000)
        .execute()
    )
    rows = result.data or []

    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        name = row["agent_name"]
        if name not in buckets:
            buckets[name] = {"agent_name": name, "total_calls": 0, "_durations": []}
        buckets[name]["total_calls"] += 1
        if row.get("duration_ms") is not None:
            buckets[name]["_durations"].append(row["duration_ms"])

    agents = []
    for data in buckets.values():
        durations = data.pop("_durations")
        data["avg_duration_ms"] = int(sum(durations) / len(durations)) if durations else 0
        agents.append(data)

    return {"agents": agents}


async def fetch_daily_activity(settings: Settings, days: int = 14) -> list[dict[str, Any]]:
    """Daily message counts for the last N days, returned oldest → newest."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    client = _get_client(settings)
    result = await asyncio.to_thread(
        lambda: client.table("messages")
        .select("created_at")
        .gte("created_at", cutoff)
        .order("created_at", desc=False)
        .execute()
    )

    counts: dict[str, int] = {}
    for row in result.data or []:
        date = row["created_at"][:10]
        counts[date] = counts.get(date, 0) + 1

    return [{"date": d, "count": c} for d, c in sorted(counts.items())]
