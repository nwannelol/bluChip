"""Admin API endpoints.

GET  /api/v1/admin/agents           — list all 4 agents with live/stub status
GET  /api/v1/admin/logs             — recent agent_logs (filterable by agent)
POST /api/v1/admin/knowledge/refresh — trigger Firecrawl web ingest in background
"""

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.config import Settings
from app.dependencies import get_settings
from app.models.schemas import AgentInfo, AgentLogEntry, KnowledgeRefreshResponse
from app.services import supabase as db

logger = logging.getLogger("nexus.api.admin")

router = APIRouter()

_AGENTS: list[AgentInfo] = [
    AgentInfo(
        name="fan",
        display_name="Fan Agent",
        description="SONA — answers fan questions about Sporting Lagos FC",
        status="active",
        is_stub=False,
    ),
    AgentInfo(
        name="media",
        display_name="Media Agent",
        description="Match coverage, press releases, and club content",
        status="stub",
        is_stub=True,
    ),
    AgentInfo(
        name="scout",
        display_name="Scout Agent",
        description="Player analysis, transfer intelligence, opposition scouting",
        status="stub",
        is_stub=True,
    ),
    AgentInfo(
        name="ops",
        display_name="Ops Agent",
        description="Club operations, scheduling, and logistics",
        status="stub",
        is_stub=True,
    ),
]


@router.get("/admin/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    """Return the status of all four NEXUS agents."""
    return _AGENTS


@router.get("/admin/logs", response_model=list[AgentLogEntry])
async def get_logs(
    limit: int = Query(default=50, ge=1, le=200),
    agent: Optional[str] = Query(default=None),
    settings: Settings = Depends(get_settings),
) -> list[AgentLogEntry]:
    """Return recent agent action logs, newest first."""
    rows = await db.fetch_agent_logs(settings, limit=limit, agent_name=agent)
    return [AgentLogEntry(**row) for row in rows]


@router.post("/admin/knowledge/refresh", response_model=KnowledgeRefreshResponse)
async def refresh_knowledge(
    settings: Settings = Depends(get_settings),
) -> KnowledgeRefreshResponse:
    """Trigger a Firecrawl web ingest in the background.

    Returns immediately — ingest runs asynchronously (~60s to complete).
    """
    async def _run() -> None:
        try:
            from app.seed.ingest_web import run
            await run(settings)
            logger.info("Background knowledge refresh complete")
        except Exception as exc:
            logger.error("Background knowledge refresh failed: %s", exc)

    asyncio.create_task(_run())
    return KnowledgeRefreshResponse(
        status="accepted",
        message="Knowledge refresh started in background. Check logs for progress.",
    )
