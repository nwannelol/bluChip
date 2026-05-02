"""Scout Agent tools — web scraping and transfer search.

Each tool is a standalone async factory so settings can be injected
without global singletons. Import make_scout_tools() into the agent.
"""

from typing import Any

from langchain_core.tools import tool

from app.config import Settings
from app.services import firecrawl


def make_scout_tools(settings: Settings) -> list[Any]:
    """Return Scout Agent tools bound to the given settings."""

    @tool
    async def scrape_player(url: str) -> str:
        """Scrape an NPFL player profile or stats page and return markdown.

        Use this when you have a direct URL to a player profile,
        club roster page, or NPFL stats page.

        Args:
            url: Full URL of the page to scrape.
        """
        content = await firecrawl.scrape(url, settings)
        if not content:
            return "Could not retrieve content from that URL."
        return content

    @tool
    async def search_transfers(query: str) -> str:
        """Search the web for NPFL transfer news and return article text.

        Use this for open-ended transfer queries such as
        'Sporting Lagos FC new signing 2025'.

        Args:
            query: Search query describing the transfer news to find.
        """
        results = await firecrawl.search(query, settings, limit=5)
        if not results:
            return "No transfer news found for that query."

        parts: list[str] = []
        for item in results:
            title = item.get("title", item.get("url", ""))
            markdown = item.get("markdown", "").strip()
            if markdown:
                parts.append(f"### {title}\n\n{markdown}")

        return "\n\n---\n\n".join(parts) if parts else "No content retrieved."

    return [scrape_player, search_transfers]
