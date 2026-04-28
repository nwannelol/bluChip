"""Fan Agent — SONA, the official AI assistant for Sporting Lagos FC.

Fully implemented in Phase 1. Uses RAG to ground every answer in the
club knowledge base, maintains conversation history, and logs all actions.
"""

import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.base import BaseAgent
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

    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """Handle a fan message end-to-end.

        Steps:
        1. Retrieve relevant knowledge base chunks (RAG)
        2. Build prompt with system message + history + context + user message
        3. Call LLM
        4. Persist conversation + log action
        5. Return updated state
        """
        message: str = state["message"]
        session_id: str = state["session_id"]
        channel: str = state.get("channel", "web")
        history: list = state.get("conversation_history", [])

        start = time.monotonic()

        # ── 1. RAG retrieval ──────────────────────────────────────────────────
        docs = await retrieve(message, self.settings, match_threshold=0.4, match_count=5)
        context_text = _format_context(docs)
        sources = [
            {"content": d["content"][:120], "metadata": d.get("metadata", {})}
            for d in docs
        ]

        # ── 2. Build messages ─────────────────────────────────────────────────
        system_content = SYSTEM_PROMPT
        if context_text:
            system_content += f"\n\n## Knowledge Base Context\n{context_text}"

        messages = [SystemMessage(content=system_content)]

        for turn in history[-10:]:  # last 5 exchanges (10 messages)
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=message))

        # ── 3. LLM call ───────────────────────────────────────────────────────
        llm = get_llm(self.settings)
        response = await llm.ainvoke(messages)
        answer: str = response.content

        duration_ms = int((time.monotonic() - start) * 1000)

        # ── 4. Persist conversation + audit log ───────────────────────────────
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

        # ── 5. Return updated state ───────────────────────────────────────────
        return {
            **state,
            "agent_response": answer,
            "retrieved_docs": docs,
            "sources": sources,
            "error": None,
        }


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
