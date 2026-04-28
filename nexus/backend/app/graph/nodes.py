"""NEXUS LangGraph node functions.

Each node wraps one agent. Settings are injected via closure so LangGraph
receives plain `(state) -> state` callables with no extra arguments.
"""

from typing import Any

from app.agents.fan.agent import FanAgent
from app.agents.media.agent import MediaAgent
from app.agents.ops.agent import OpsAgent
from app.agents.scout.agent import ScoutAgent
from app.config import Settings


def make_nodes(settings: Settings) -> dict[str, Any]:
    """Return a dict of node callables with settings closed over."""
    fan = FanAgent(settings)
    media = MediaAgent(settings)
    scout = ScoutAgent(settings)
    ops = OpsAgent(settings)

    async def run_fan(state: dict[str, Any]) -> dict[str, Any]:
        return await fan.process(state)

    async def run_media(state: dict[str, Any]) -> dict[str, Any]:
        return await media.process(state)

    async def run_scout(state: dict[str, Any]) -> dict[str, Any]:
        return await scout.process(state)

    async def run_ops(state: dict[str, Any]) -> dict[str, Any]:
        return await ops.process(state)

    return {
        "fan": run_fan,
        "media": run_media,
        "scout": run_scout,
        "ops": run_ops,
    }


def route_message(state: dict[str, Any]) -> str:
    """Conditional edge: map state.target_agent to the correct node name."""
    agent = state.get("target_agent", "fan")
    return agent if agent in {"fan", "media", "scout", "ops"} else "fan"
