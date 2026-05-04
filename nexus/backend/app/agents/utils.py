"""Shared utilities for NEXUS agents."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def build_history_messages(history: list, limit: int = 10) -> list[BaseMessage]:
    """Convert stored conversation history to LangChain message objects."""
    messages: list[BaseMessage] = []
    for turn in history[-limit:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages
