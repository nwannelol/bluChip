"""Scout Agent — player analysis and transfer intelligence for Sporting Lagos FC.

Grounded in live web data retrieved via Firecrawl search.
Never fabricates player stats, transfer fees, or club data.
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.agents.utils import build_history_messages
from app.config import Settings
from app.services import firecrawl, supabase as db
from app.services.llm import get_llm

logger = logging.getLogger("nexus.agent.scout")

SYSTEM_PROMPT = """You are the Scout Agent for Sporting Lagos FC — a global football \
intelligence analyst identifying talent and transfer opportunities that can elevate the club.

Your role:
- Research player profiles, stats, and performance data from any league worldwide
- Identify players who could realistically benefit Sporting Lagos FC (NPFL budget, club ambition, player profile fit)
- Track transfer window activity and rumours globally and within Nigeria
- Provide opposition scouting reports for NPFL fixtures
- Monitor emerging talent across Africa, Europe, and beyond

Ground rules:
- You are grounded ONLY in data retrieved from the web. If you don't have specific data,
  say so clearly — never fabricate player stats, transfer fees, or club information.
- Be analytical, precise, and concise. Use numbers and facts when available.
- Always indicate the source of information when possible.
- Consider players from any league — the best signing for Sporting Lagos may come from the
  NPFL, another African league, a lower European division, or the diaspora."""


class ScoutAgent(BaseAgent):
    """Scout Agent — player analysis and transfers powered by Firecrawl web search."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(name="scout", description="Scout Agent — player analysis & transfers")
        self.settings = settings

    async def _prepare_inputs(
        self, message: str, history: list
    ) -> tuple[list, list[dict[str, Any]], list]:
        """Run Firecrawl search and build the LLM message list.

        Returns (messages, sources, raw_results).
        """
        try:
            raw = await firecrawl.search(f"football {message}", self.settings, limit=5)
            parts: list[str] = []
            sources: list[dict[str, Any]] = []
            for item in raw:
                title = item.get("title", item.get("url", ""))
                markdown = (item.get("markdown") or "").strip()[:1500]
                url = item.get("url", "")
                if markdown:
                    parts.append(f"### {title}\n{markdown}")
                    sources.append({"content": markdown[:120], "metadata": {"title": title, "url": url}})
            context_text = "\n\n---\n\n".join(parts)
        except Exception as exc:
            logger.warning("Firecrawl search failed for scout query: %s", exc)
            raw, context_text, sources = [], "", []

        system_content = SYSTEM_PROMPT
        if context_text:
            system_content += f"\n\n## Retrieved Web Context\n{context_text}"

        messages = [SystemMessage(content=system_content)]
        messages.extend(build_history_messages(history))
        messages.append(HumanMessage(content=message))

        return messages, sources, raw

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Handle a scouting query end-to-end."""
        message: str = state["message"]
        session_id: str = state["session_id"]
        channel: str = state.get("channel", "web")
        history: list = state.get("conversation_history", [])

        start = time.monotonic()
        messages, sources, raw = await self._prepare_inputs(message, history)

        llm = get_llm(self.settings)
        response = await llm.ainvoke(messages)
        answer: str = response.content
        duration_ms = int((time.monotonic() - start) * 1000)

        try:
            conv = await db.get_or_create_conversation(session_id, channel, self.settings)
            await db.save_message(conv["id"], "user", message, "scout", [], self.settings)
            await db.save_message(conv["id"], "assistant", answer, "scout", sources, self.settings)
        except Exception as exc:
            logger.warning("Failed to persist Scout conversation: %s", exc)

        await db.log_agent_action(
            agent_name="scout",
            session_id=session_id,
            action="llm_call",
            input_data={"message": message, "results_retrieved": len(raw)},
            output_data={"response_length": len(answer)},
            settings=self.settings,
            duration_ms=duration_ms,
        )

        return {**state, "agent_response": answer, "retrieved_docs": raw, "sources": sources, "error": None}

    async def stream(self, state: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Yield LLM response tokens one at a time.

        Firecrawl search runs up front (blocking but fast), then tokens
        stream directly. Persistence fires in the background after the
        last token so the caller can send [DONE] without waiting.
        """
        message: str = state["message"]
        session_id: str = state["session_id"]
        channel: str = state.get("channel", "web")
        history: list = state.get("conversation_history", [])

        start = time.monotonic()
        messages, sources, raw = await self._prepare_inputs(message, history)

        llm = get_llm(self.settings)
        full_tokens: list[str] = []
        async for chunk in llm.astream(messages):
            token: str = chunk.content
            if token:
                full_tokens.append(token)
                yield token

        answer = "".join(full_tokens)
        duration_ms = int((time.monotonic() - start) * 1000)

        async def _persist() -> None:
            try:
                conv = await db.get_or_create_conversation(session_id, channel, self.settings)
                await db.save_message(conv["id"], "user", message, "scout", [], self.settings)
                await db.save_message(conv["id"], "assistant", answer, "scout", sources, self.settings)
            except Exception as exc:
                logger.warning("Failed to persist streamed Scout conversation: %s", exc)
            await db.log_agent_action(
                agent_name="scout",
                session_id=session_id,
                action="llm_stream",
                input_data={"message": message, "results_retrieved": len(raw)},
                output_data={"response_length": len(answer)},
                settings=self.settings,
                duration_ms=duration_ms,
            )

        asyncio.create_task(_persist())
