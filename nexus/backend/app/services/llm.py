"""LLM service wrapper.

All agent LLM calls go through get_llm() — never import ChatGroq directly
in agent files.
"""

from langchain_groq import ChatGroq

from app.config import Settings


def get_llm(settings: Settings) -> ChatGroq:
    """Return a ChatGroq instance bound to the current settings.

    Args:
        settings: Injected application settings.

    Returns:
        Configured ChatGroq client ready for agent use.
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.llm_model,
        temperature=0.7,
        max_retries=2,
    )
