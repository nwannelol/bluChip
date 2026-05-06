"""Fan Agent — SONA, the official AI assistant for Sporting Lagos FC."""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
from app.agents.utils import build_history_messages
from app.config import Settings
from app.rag.retriever import retrieve
from app.services import supabase as db
from app.services.llm import get_llm

logger = logging.getLogger("nexus.agent.fan")

SYSTEM_PROMPT = """You are SONA, the official AI assistant for Sporting Lagos FC —
nicknamed "The Tech Boys" and "The Noisy Lagosians". You were built
to serve the club's fans with pride and energy.

You know everything about Sporting Lagos:
- Founded February 3, 2022 by Shola Akinlade (co-founder of Paystack)
- Play at Mobolaji Johnson Arena (Onikan Stadium), Lagos
- Colors: Neon Blue and Pantone Blue (home), Yellow (away)
- Captain: Abdulraheem Suleiman (#8)
- Head Coach: Jeffrey Buter
- Big rivals: Remo Stars FC and Ikorodu City FC
- Academy won the Gothia Cup U17 in Sweden (2024)
- Ebenezer Harcourt became Nigeria's youngest senior international (2025)

Personality: passionate, Lagos-proud, warm, knowledgeable.
Speak like a true Sporting Lagos fan. Use "we" and "our" when referring
to the club. Keep answers concise and energetic. If you don't know
something, say so honestly rather than making it up.

Always use context retrieved from the knowledge base before answering."""


class FanAgent(BaseAgent):
    """Fully implemented Fan Agent — answers fan questions about Sporting Lagos FC."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(name="fan", description="SONA — Sporting Lagos FC fan assistant")
        self.settings = settings

    async def _prepare_inputs(
        self, message: str, history: list
    ) -> tuple[list, list[dict], list]:
        """Run RAG retrieval and build the LLM message list.

        Returns (messages, sources, raw_docs).
        """
        docs = await retrieve(message, self.settings, match_threshold=0.4, match_count=8)
        context_text = _format_context(docs)
        sources = [
            {"content": d["content"][:120], "metadata": d.get("metadata", {})}
            for d in docs
        ]

        system_content = SYSTEM_PROMPT
        if context_text:
            system_content += f"\n\n## Knowledge Base Context\n{context_text}"

        messages = [SystemMessage(content=system_content)]
        messages.extend(build_history_messages(history))
        messages.append(HumanMessage(content=message))

        return messages, sources, docs

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Handle a fan message end-to-end (non-streaming)."""
        message: str = state["message"]
        session_id: str = state["session_id"]
        channel: str = state.get("channel", "web")
        history: list = state.get("conversation_history", [])

        start = time.monotonic()
        messages, sources, docs = await self._prepare_inputs(message, history)

        llm = get_llm(self.settings)
        response = await llm.ainvoke(messages)
        answer: str = response.content
        duration_ms = int((time.monotonic() - start) * 1000)

        try:
            conv = await db.get_or_create_conversation(session_id, channel, self.settings)
            await db.save_message(conv["id"], "user", message, "fan", [], self.settings)
            await db.save_message(conv["id"], "assistant", answer, "fan", sources, self.settings)
        except Exception as exc:
            logger.warning("Failed to persist conversation: %s", exc)

        await db.log_agent_action(
            agent_name="fan",
            session_id=session_id,
            action="llm_call",
            input_data={"message": message, "docs_retrieved": len(docs)},
            output_data={"response_length": len(answer)},
            settings=self.settings,
            duration_ms=duration_ms,
        )

        return {**state, "agent_response": answer, "retrieved_docs": docs, "sources": sources, "error": None}

    async def stream(self, state: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Yield LLM response tokens one at a time.

        Persistence fires in the background after the last token so the
        caller can send [DONE] without waiting for DB writes to complete.
        """
        message: str = state["message"]
        session_id: str = state["session_id"]
        channel: str = state.get("channel", "web")
        history: list = state.get("conversation_history", [])

        start = time.monotonic()
        messages, sources, docs = await self._prepare_inputs(message, history)

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
                await db.save_message(conv["id"], "user", message, "fan", [], self.settings)
                await db.save_message(conv["id"], "assistant", answer, "fan", sources, self.settings)
            except Exception as exc:
                logger.warning("Failed to persist streamed conversation: %s", exc)
            await db.log_agent_action(
                agent_name="fan",
                session_id=session_id,
                action="llm_stream",
                input_data={"message": message, "docs_retrieved": len(docs)},
                output_data={"response_length": len(answer)},
                settings=self.settings,
                duration_ms=duration_ms,
            )

        asyncio.create_task(_persist())


def _format_context(docs: list[dict[str, Any]]) -> str:
    """Format retrieved docs into a readable context block for the LLM."""
    if not docs:
        return ""
    parts = []
    for doc in docs:
        title = doc.get("metadata", {}).get("title", "")
        content = doc["content"].strip()
        parts.append(f"**{title}**\n{content}" if title else content)
    return "\n\n---\n\n".join(parts)
