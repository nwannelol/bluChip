"""Scout Agent — stub for Phase 1.

Handles player analysis, transfer intelligence, and opposition scouting.
Returns is_stub indicator until fully implemented in Phase 2.
"""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.config import Settings
from app.services import supabase as db

logger = logging.getLogger("nexus.agent.scout")

_STUB_RESPONSE = (
    "The Scout Agent is coming soon! Player profiles, transfer intelligence, "
    "and opposition analysis for Sporting Lagos FC are on the way."
)


class ScoutAgent(BaseAgent):
    """Stub Scout Agent — player analysis and transfers (Phase 2)."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(name="scout", description="Scout Agent — player analysis & transfers (stub)")
        self.settings = settings

    @property
    def is_stub(self) -> bool:
        return True

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("ScoutAgent stub invoked for session %s", state.get("session_id"))
        await db.log_agent_action(
            agent_name="scout",
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
