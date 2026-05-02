"""Seed the Supabase knowledge_base with Sporting Lagos FC club data.

Usage (from cil/backend/):
    python -m app.seed.seed_db

Requires a valid .env file with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.
Safe to re-run — clears the "club_data" source before inserting.
"""

import asyncio
import json
import logging
from pathlib import Path

from app.config import Settings
from app.rag.ingest import clear_source, ingest_document

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("cil.seed")

DATA_FILE = Path(__file__).parent / "club_data.json"


async def run() -> None:
    settings = Settings()

    logger.info("Clearing existing club_data from knowledge_base...")
    await clear_source("club_data", settings)

    with DATA_FILE.open() as f:
        documents: list[dict] = json.load(f)

    total_chunks = 0
    for doc in documents:
        chunks = await ingest_document(
            content=doc["content"],
            metadata={
                "source": "club_data",
                "category": doc.get("category", "general"),
                "title": doc.get("title", ""),
            },
            settings=settings,
        )
        total_chunks += chunks
        logger.info("  ✓ %s (%d chunks)", doc["title"], chunks)

    logger.info("Seed complete — %d documents, %d chunks total", len(documents), total_chunks)


if __name__ == "__main__":
    asyncio.run(run())
