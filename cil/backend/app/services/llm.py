"""LLM service — single source of truth for all LLM access.

Agent files must import get_llm() from here; never import langchain_groq directly.
"""

from langchain_groq import ChatGroq

from app.config import Settings

_llm: ChatGroq | None = None


def get_llm(settings: Settings | None = None) -> ChatGroq:
    """Return a module-level ChatGroq singleton."""
    global _llm
    if _llm is None:
        cfg = settings or Settings()
        _llm = ChatGroq(
            model=cfg.llm_model,
            api_key=cfg.groq_api_key,
            temperature=0.3,
            max_retries=2,
        )
    return _llm
