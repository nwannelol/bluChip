"""Analytics endpoints — fan engagement metrics for the investor dashboard.

GET /api/v1/analytics/summary  — aggregate counts (conversations, messages, fans)
GET /api/v1/analytics/agents   — per-agent call count and avg response time
GET /api/v1/analytics/activity — daily message counts for the last N days
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.config import Settings
from app.dependencies import get_settings, require_admin_key
from app.services import supabase as db

logger = logging.getLogger("nexus.api.analytics")

router = APIRouter()


@router.get("/analytics/summary")
async def get_summary(
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_admin_key),
) -> dict[str, Any]:
    """Aggregate engagement metrics: conversations, messages, fans, channel breakdown."""
    return await db.fetch_analytics_summary(settings)


@router.get("/analytics/agents")
async def get_agent_stats(
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_admin_key),
) -> dict[str, Any]:
    """Per-agent call count and average response time from agent_logs."""
    return await db.fetch_agent_stats(settings)


@router.get("/analytics/activity")
async def get_daily_activity(
    days: int = Query(default=14, ge=1, le=90),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_admin_key),
) -> list[dict[str, Any]]:
    """Daily message counts for the last N days — sparkline data for dashboards."""
    return await db.fetch_daily_activity(settings, days=days)
