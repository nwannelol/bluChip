"""FastAPI dependency injection.

Use these in route functions via `Depends()`.
"""

from functools import lru_cache

from app.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (reads .env once)."""
    return Settings()
