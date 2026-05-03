"""Web scrape ingest — enriches the knowledge base with live data from
authoritative sources via Firecrawl.

Clears previous web_scrape entries then re-ingests fresh content.
Run: python -m app.seed.ingest_web  (from nexus/backend/)
"""

import asyncio
import logging

from app.config import Settings
from app.rag.ingest import clear_source, ingest_document
from app.services import firecrawl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("nexus.seed.web")

SCRAPE_URLS = [
    {
        "url": "https://sportinglagos.com",
        "title": "Sporting Lagos — Official Website",
        "category": "identity",
    },
    {
        "url": "https://en.wikipedia.org/wiki/Sporting_Lagos_F.C.",
        "title": "Sporting Lagos FC — Wikipedia",
        "category": "history",
    },
    {
        "url": "https://npfl.com.ng",
        "title": "NPFL — Nigeria Premier Football League",
        "category": "competition",
    },
    {
        "url": "https://edition.cnn.com/2022/04/20/football/shola-akinlade-paystack-sporting-lagos-spc-intl/index.html",
        "title": "CNN — Shola Akinlade: The Paystack co-founder building a football club",
        "category": "history",
    },
]

SEARCH_QUERIES = [
    {"query": "Sporting Lagos FC NPFL 2025 season results",   "category": "competition"},
    {"query": "Jeffrey Buter Sporting Lagos head coach",       "category": "management"},
    {"query": "Abdulraheem Suleiman Sporting Lagos captain",   "category": "squad"},
    {"query": "Sporting Lagos FC news transfers 2025",         "category": "transfers"},
]


async def run(settings: Settings) -> None:
    logger.info("Clearing previous web_scrape entries…")
    await clear_source("web_scrape", settings)

    # ── Direct URL scrapes ────────────────────────────────────────────────────
    for item in SCRAPE_URLS:
        logger.info("Scraping %s", item["url"])
        try:
            content = await firecrawl.scrape(item["url"], settings)
            if content.strip():
                chunks = await ingest_document(
                    content,
                    {
                        "source": "web_scrape",
                        "category": item["category"],
                        "title": item["title"],
                        "url": item["url"],
                    },
                    settings,
                )
                logger.info("  ✓ %s — %d chunks", item["title"], chunks)
            else:
                logger.warning("  ✗ %s — empty response", item["url"])
        except Exception as exc:
            logger.error("  ✗ %s — %s", item["url"], exc)

    # ── Search queries ────────────────────────────────────────────────────────
    for item in SEARCH_QUERIES:
        logger.info("Searching: %s", item["query"])
        try:
            results = await firecrawl.search(item["query"], settings, limit=5)
            total = 0
            for r in results:
                md = r.get("markdown", "").strip()
                if not md:
                    continue
                chunks = await ingest_document(
                    md,
                    {
                        "source": "web_scrape",
                        "category": item["category"],
                        "title": r.get("title", item["query"]),
                        "url": r.get("url", ""),
                    },
                    settings,
                )
                total += chunks
            logger.info("  ✓ %d chunks from %d results", total, len(results))
        except Exception as exc:
            logger.error("  ✗ %s — %s", item["query"], exc)

    logger.info("Web ingest complete.")


if __name__ == "__main__":
    asyncio.run(run(Settings()))
