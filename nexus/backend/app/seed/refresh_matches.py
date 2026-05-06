"""Scheduled matches refresh — scrapes the live matches page and upserts
fresh data into the knowledge base.

Runs on startup and then every hour via APScheduler (wired in main.py).
Uses a dedicated source tag "matches_live" so only matches rows are replaced,
leaving all other web_scrape content intact.
"""

import asyncio
import logging

from app.config import Settings
from app.rag.ingest import clear_source, ingest_document
from app.services import firecrawl

logger = logging.getLogger("nexus.seed.matches")

MATCHES_URL = "https://www.sportinglagos.com/matches"


async def refresh_matches(settings: Settings | None = None) -> int:
    """Scrape the matches page and replace knowledge base rows for it.

    Returns the number of chunks ingested (0 on failure).
    """
    if settings is None:
        settings = Settings()

    logger.info("Refreshing matches knowledge from %s", MATCHES_URL)
    try:
        content = await firecrawl.scrape(MATCHES_URL, settings)
        if not content.strip():
            logger.warning("Matches page returned empty content — skipping refresh")
            return 0

        await clear_source("matches_live", settings)

        chunks = await ingest_document(
            content,
            {
                "source": "matches_live",
                "category": "competition",
                "title": "Sporting Lagos FC — Fixtures & Results (Live)",
                "url": MATCHES_URL,
            },
            settings,
        )
        logger.info("Matches refresh complete — %d chunks ingested", chunks)
        return chunks

    except Exception as exc:
        logger.error("Matches refresh failed: %s", exc)
        return 0


if __name__ == "__main__":
    asyncio.run(refresh_matches())
