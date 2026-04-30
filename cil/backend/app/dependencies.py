"""FastAPI dependency injection.

Use these in route functions via `Depends()`.
"""

from functools import lru_cache

from langchain_groq import ChatGroq
from supabase import AsyncClient

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (reads .env once)."""
    return Settings()


async def get_db() -> AsyncClient:
    """Return the Supabase async client singleton."""
    from app.services.supabase import get_supabase

    return await get_supabase(get_settings())


def get_llm() -> ChatGroq:
    """Return the ChatGroq singleton."""
    from app.services.llm import get_llm as _get_llm

    return _get_llm(get_settings())
