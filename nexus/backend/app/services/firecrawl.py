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


async def crawl(
    start_url: str,
    settings: Settings,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Crawl a site starting from start_url, following internal links.

    Returns up to `limit` pages as dicts with keys: url, markdown.
    Polls until the crawl job completes (handled by the SDK).
    """
    v1 = _get_client(settings)._v1_client

    result = await asyncio.to_thread(
        v1.crawl_url,
        start_url,
        limit=limit,
        scrape_options=V1ScrapeOptions(formats=["markdown"]),
    )

    pages = getattr(result, "data", None) or []

    out = []
    for page in pages:
        if isinstance(page, dict):
            out.append(page)
        else:
            out.append({
                "url": getattr(page, "url", ""),
                "markdown": getattr(page, "markdown", "") or "",
            })
    return out
