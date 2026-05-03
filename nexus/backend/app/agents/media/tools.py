"""Media Agent tools — match coverage search.

Each tool is a standalone async factory so settings can be injected
without global singletons. Import make_media_tools() into the agent.
"""

from typing import Any

from langchain_core.tools import tool

from app.config import Settings
from app.services import firecrawl


def make_media_tools(settings: Settings) -> list[Any]:
    """Return Media Agent tools bound to the given settings."""

    @tool
    async def search_match_coverage(query: str) -> str:
        """Search for post-match articles and return their full text.

        Use this to find match reports, press conference quotes, and
        post-game analysis for Sporting Lagos FC fixtures.

        Args:
            query: Search query, e.g. 'Sporting Lagos vs Remo Stars match report'.
        """
        results = await firecrawl.search(query, settings, limit=5)
        if not results:
            return "No match coverage found for that query."

        parts: list[str] = []
        for item in results:
            title = item.get("title", item.get("url", ""))
            markdown = item.get("markdown", "").strip()
            if markdown:
                parts.append(f"### {title}\n\n{markdown}")

        return "\n\n---\n\n".join(parts) if parts else "No content retrieved."

    return [search_match_coverage]
