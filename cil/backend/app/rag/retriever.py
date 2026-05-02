"""RAG retriever — queries the Supabase knowledge_base via cosine similarity.

The Fan Agent calls retrieve() to get relevant context before calling the LLM.
"""

import asyncio
from typing import Any

from supabase import create_client

from app.config import Settings
from app.rag.embeddings import embed_text


async def retrieve(
    query: str,
    settings: Settings,
    match_threshold: float = 0.5,
    match_count: int = 5,
) -> list[dict[str, Any]]:
    """Find the most relevant knowledge_base chunks for a query.

    Args:
        query: The user's question or search string.
        settings: Injected application settings.
        match_threshold: Minimum cosine similarity (0–1). Lower = broader results.
        match_count: Maximum number of chunks to return.

    Returns:
        List of dicts with keys: id, content, metadata, similarity.
    """
    embedding = embed_text(query)
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    result = await asyncio.to_thread(
        lambda: client.rpc(
            "match_knowledge_base",
            {
                "query_embedding": embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
            },
        ).execute()
    )

    return result.data or []
