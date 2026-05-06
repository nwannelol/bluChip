"""FastAPI dependency injection.

Use these in route functions via `Depends()`.
"""

from functools import lru_cache

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import Settings

_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (reads .env once)."""
    return Settings()


def require_admin_key(
    key: str | None = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> None:
    """Reject requests that don't carry the correct X-Admin-Key header.

    If ADMIN_API_KEY is not configured, the check is skipped (dev mode).
    """
    configured = settings.admin_api_key
    if configured and key != configured:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-Admin-Key header.",
        )


@lru_cache
def get_graph():
    """Return the compiled NEXUS LangGraph (built once, reused on every request)."""
    from app.graph.orchestrator import build_graph
    return build_graph(get_settings())
