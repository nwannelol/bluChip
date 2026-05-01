"""Firecrawl web-scraping service wrapper.

Agents call `scrape()` and `search()` from here.
Never import FirecrawlApp directly in agent or tool files.
"""

import asyncio
from typing import Any

from firecrawl import FirecrawlApp

from app.config import Settings


def _get_client(settings: Settings) -> FirecrawlApp:
    return FirecrawlApp(
        api_key=settings.firecrawl_key,
        api_url=settings.firecrawl_url,
    )


async def scrape(url: str, settings: Settings) -> str:
    """Scrape a single URL and return its content as markdown.

    Args:
        url: The URL to fetch.
        settings: Injected application settings.

    Returns:
        Markdown string of the page content, or empty string on failure.
    """
    client = _get_client(settings)
    result: dict[str, Any] = await asyncio.to_thread(
        client.scrape_url,
        url,
        params={"formats": ["markdown"]},
    )
    return result.get("markdown", "")


async def search(
    query: str,
    settings: Settings,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Search the web and return scraped results.

    Args:
        query: Search query string.
        settings: Injected application settings.
        limit: Maximum number of results to return.

    Returns:
        List of dicts, each with keys: url, title, markdown.
    """
    client = _get_client(settings)
    result: dict[str, Any] = await asyncio.to_thread(
        client.search,
        query,
        params={
            "limit": limit,
            "scrapeOptions": {"formats": ["markdown"]},
        },
    )
    return result.get("data", [])
