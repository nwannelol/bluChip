"""NEXUS shared state for LangGraph.

All agents read and write to this TypedDict so the graph
can route messages between them.
"""

from typing import Optional, TypedDict


class NEXUSState(TypedDict):
    """Shared state that flows through the LangGraph orchestrator."""

    message: str
    channel: str                    # "web" | "whatsapp"
    session_id: str
    target_agent: str               # "fan" | "media" | "scout" | "ops"
    conversation_history: list
    retrieved_docs: list            # RAG results for Fan Agent
    agent_response: str
    sources: list
    error: Optional[str]
