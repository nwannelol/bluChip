"""RAG ingest pipeline — chunks documents and loads them into knowledge_base.

Run seed/seed_db.py which calls ingest_document() for each piece of
Sporting Lagos club data.
"""

import asyncio
import logging
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter
from supabase import create_client

from app.config import Settings
from app.rag.embeddings import embed_texts

logger = logging.getLogger("cil.rag.ingest")

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks suitable for embedding."""
    return _splitter.split_text(text)


async def ingest_document(
    content: str,
    metadata: dict[str, Any],
    settings: Settings,
) -> int:
    """Chunk a document, embed each chunk, and insert into knowledge_base.

    Args:
        content: Raw text content to ingest.
        metadata: Dict stored alongside each chunk — include at minimum
                  {"source": "...", "category": "..."}.
        settings: Injected application settings.

    Returns:
        Number of chunks inserted.
    """
    chunks = chunk_text(content)
    if not chunks:
        return 0

    embeddings = embed_texts(chunks)

    rows = [
        {"content": chunk, "metadata": metadata, "embedding": emb}
        for chunk, emb in zip(chunks, embeddings)
    ]

    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    await asyncio.to_thread(
        lambda: client.table("knowledge_base").insert(rows).execute()
    )

    logger.info("Ingested %d chunks | source=%s", len(rows), metadata.get("source"))
    return len(rows)


async def clear_source(source: str, settings: Settings) -> None:
    """Delete all chunks from a given source (for re-ingestion).

    Args:
        source: The metadata.source value to clear, e.g. "club_data".
        settings: Injected application settings.
    """
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    await asyncio.to_thread(
        lambda: client.table("knowledge_base")
        .delete()
        .eq("metadata->>source", source)
        .execute()
    )
    logger.info("Cleared knowledge_base for source=%s", source)
