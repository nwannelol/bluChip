"""Embedding generation using all-MiniLM-L6-v2.

The model is loaded once and cached for the process lifetime.
Embedding dim = 384 — must match the knowledge_base table schema.
"""

from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """Embed a single string. Returns a 384-dim float list."""
    return _get_model().encode(text, convert_to_numpy=True).tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of strings. More efficient than calling embed_text in a loop."""
    return _get_model().encode(texts, convert_to_numpy=True).tolist()
