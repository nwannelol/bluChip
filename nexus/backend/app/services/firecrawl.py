"""Firecrawl web-scraping service wrapper.

Agents call `scrape()` and `search()` from here.
Never import FirecrawlApp directly in agent or tool files.

SDK: firecrawl-py v4 — uses _v1_client with keyword args, returns Pydantic models.
"""

import asyncio
from typing import Any

from firecrawl import FirecrawlApp
from firecrawl.v1.client import V1ScrapeOptions

from app.config import Settings


def _get_client(settings: Settings) -> FirecrawlApp:
    return FirecrawlApp(
        api_key=settings.firecrawl_key,
        api_url=settings.firecrawl_url,
    )


async def scrape(url: str, settings: Settings) -> str:
    """Scrape a single URL and return its content as markdown."""
    v1 = _get_client(settings)._v1_client
    result = await asyncio.to_thread(
        v1.scrape_url,
        url,
        formats=["markdown"],
    )
    return result.markdown or ""


async def search(
    query: str,
    settings: Settings,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search the web and return scraped results.

    Returns:
        List of dicts with keys: url, title, markdown.
    """
    v1 = _get_client(settings)._v1_client
    result = await asyncio.to_thread(
        v1.search,
        query,
        limit=limit,
        scrape_options=V1ScrapeOptions(formats=["markdown"]),
    )
    return result.data or []
