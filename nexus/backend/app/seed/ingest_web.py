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

# ── Direct scrape URLs (single-page, static content) ─────────────────────────
# Firecrawl uses a headless browser so JS-rendered pages and anti-bot
# protections (e.g. Transfermarkt) are handled automatically.

SCRAPE_URLS = [
    # Official club pages
    {
        "url": "https://www.sportinglagos.com/club-info/whoswho",
        "title": "Sporting Lagos — Who's Who (Staff & Personnel)",
        "category": "management",
    },
    {
        "url": "https://www.sportinglagos.com/club-info/clubhistory",
        "title": "Sporting Lagos — Club History",
        "category": "history",
    },
    {
        "url": "https://www.sportinglagos.com/players",
        "title": "Sporting Lagos — Full Squad",
        "category": "squad",
    },
    # Wikipedia baseline
    {
        "url": "https://en.wikipedia.org/wiki/Sporting_Lagos_F.C.",
        "title": "Sporting Lagos FC — Wikipedia",
        "category": "history",
    },
    # CNN founding story
    {
        "url": "https://edition.cnn.com/2022/04/20/football/shola-akinlade-paystack-sporting-lagos-spc-intl/index.html",
        "title": "CNN — Shola Akinlade: The Paystack co-founder building a football club",
        "category": "history",
    },
    # Transfermarkt — transfer history, squad values, fixtures
    {
        "url": "https://www.transfermarkt.com/sporting-lagos-fc/alletransfers/verein/105908",
        "title": "Transfermarkt — Sporting Lagos Transfer History",
        "category": "transfers",
    },
    {
        "url": "https://www.transfermarkt.com/sporting-lagos-fc/kader/verein/105908/saison_id/2025/plus/1",
        "title": "Transfermarkt — Sporting Lagos Squad 2025",
        "category": "squad",
    },
    {
        "url": "https://www.transfermarkt.com/sporting-lagos-fc/spielplandatum/verein/105908/saison_id//wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
        "title": "Transfermarkt — Sporting Lagos Fixtures & Results",
        "category": "competition",
    },
    # Social media public pages
    {
        "url": "https://x.com/SportingLagosFC",
        "title": "Sporting Lagos FC — Twitter/X",
        "category": "news",
    },
    # Note: Facebook not supported by Firecrawl — covered via search queries instead
]

# ── Crawl targets (follows internal links, catches all articles) ──────────────
# Each entry: start URL + how many pages deep to follow.

CRAWL_TARGETS = [
    {
        "url": "https://www.sportinglagos.com/news",
        "title_prefix": "Sporting Lagos News",
        "category": "news",
        "limit": 15,
    },
]

# ── Search queries ─────────────────────────────────────────────────────────────

SEARCH_QUERIES = [
    # Existing
    {"query": "Sporting Lagos FC NPFL 2025 season results",         "category": "competition"},
    {"query": "Jeffrey Buter Sporting Lagos head coach",             "category": "management"},
    {"query": "Abdulraheem Suleiman Sporting Lagos captain",         "category": "squad"},
    {"query": "Sporting Lagos FC news transfers 2025",               "category": "transfers"},
    # New — squad & players
    {"query": "Sporting Lagos FC full squad roster 2024 2025",       "category": "squad"},
    {"query": "Sporting Lagos FC player signings transfers 2024 2025", "category": "transfers"},
    {"query": "Ebenezer Harcourt goalkeeper Nigeria Super Eagles 2025", "category": "squad"},
    # New — match data
    {"query": "Sporting Lagos FC NPFL 2025 match results scores",    "category": "competition"},
    {"query": "Sporting Lagos FC upcoming fixtures schedule 2025",   "category": "competition"},
    {"query": "NPFL season 2024 2025 standings table Nigeria",       "category": "competition"},
    # New — club details
    {"query": "Mobolaji Johnson Arena Onikan Stadium ticket prices capacity", "category": "stadium"},
    {"query": "Sporting Lagos FC sponsors partners brands Nigeria",  "category": "identity"},
    {"query": "Shola Akinlade Sporting Lagos FC investment vision 2025", "category": "history"},
    {"query": "Sporting Lagos FC news latest 2025",                  "category": "news"},
    {"query": "Sporting Lagos FC Twitter social media updates",      "category": "news"},
    {"query": "Sporting Lagos FC Facebook latest updates news",     "category": "news"},
    {"query": "Sporting Lagos FC goals scored conceded statistics season", "category": "competition"},
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

    # ── Crawl targets (follow internal links) ────────────────────────────────
    for target in CRAWL_TARGETS:
        logger.info("Crawling %s (limit=%d)", target["url"], target["limit"])
        try:
            pages = await firecrawl.crawl(target["url"], settings, limit=target["limit"])
            total_chunks = 0
            for page in pages:
                md = page.get("markdown", "").strip()
                if not md:
                    continue
                page_url = page.get("url", target["url"])
                chunks = await ingest_document(
                    md,
                    {
                        "source": "web_scrape",
                        "category": target["category"],
                        "title": f"{target['title_prefix']} — {page_url}",
                        "url": page_url,
                    },
                    settings,
                )
                total_chunks += chunks
            logger.info("  ✓ %d pages → %d chunks from %s", len(pages), total_chunks, target["url"])
        except Exception as exc:
            logger.error("  ✗ crawl %s — %s", target["url"], exc)

    # ── Search queries ────────────────────────────────────────────────────────
    for item in SEARCH_QUERIES:
        logger.info("Searching: %s", item["query"])
        try:
            results = await firecrawl.search(item["query"], settings, limit=5)
            total = 0
            for r in results:
                # Search results may be Pydantic objects or dicts
                md = (r.get("markdown", "") if isinstance(r, dict) else getattr(r, "markdown", "")) or ""
                md = md.strip()
                if not md:
                    continue
                url = (r.get("url", "") if isinstance(r, dict) else getattr(r, "url", "")) or ""
                title = (r.get("title", item["query"]) if isinstance(r, dict) else getattr(r, "title", item["query"])) or item["query"]
                chunks = await ingest_document(
                    md,
                    {
                        "source": "web_scrape",
                        "category": item["category"],
                        "title": title,
                        "url": url,
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
