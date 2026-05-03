"""Media Agent — stub for Phase 1.

Handles press releases, match coverage, and content requests.
Returns is_stub indicator until fully implemented in Phase 2.
"""

import logging
from typing import Any

from app.agents.base import BaseAgent
from app.config import Settings
from app.services import supabase as db

logger = logging.getLogger("nexus.agent.media")

_STUB_RESPONSE = (
    "The Media Agent is coming soon! We'll be delivering match reports, "
    "press releases, and content straight from Sporting Lagos FC. Watch this space."
)


class MediaAgent(BaseAgent):
    """Stub Media Agent — content and press coverage (Phase 2)."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(name="media", description="Media Agent — content & press (stub)")
        self.settings = settings

    @property
    def is_stub(self) -> bool:
        return True

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        logger.info("MediaAgent stub invoked for session %s", state.get("session_id"))
        await db.log_agent_action(
            agent_name="media",
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
