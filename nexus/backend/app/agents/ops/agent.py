"""Ops Agent — stub for Phase 1.

Handles club operations, logistics, and internal workflow requests.
Returns is_stub indicator until fully implemented in Phase 2.
"""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.config import Settings
from app.services import supabase as db

logger = logging.getLogger("nexus.agent.ops")

_STUB_RESPONSE = (
    "The Ops Agent is coming soon! Club operations, scheduling, "
    "and logistics support for Sporting Lagos FC will be available shortly."
)


class OpsAgent(BaseAgent):
    """Stub Ops Agent — club operations and logistics (Phase 2)."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(name="ops", description="Ops Agent — club operations (stub)")
        self.settings = settings

    @property
    def is_stub(self) -> bool:
        return True

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("OpsAgent stub invoked for session %s", state.get("session_id"))
        await db.log_agent_action(
            agent_name="ops",
            session_id=state.get("session_id", ""),
            action="stub_call",
            input_data={"message": state.get("message", "")},
            output_data={"is_stub": True},
            settings=self.settings,
        )
        return {
            **state,
            "agent_response": _STUB_RESPONSE,
            "retrieved_docs": [],
            "sources": [],
            "error": None,
        }
