"""
Converts text (code chunks or user questions) into vector embeddings.

Runs 100% locally via sentence-transformers -- no API key, no cost.
The model is loaded once (lazily) and reused for every request, and is
kept behind a thin function interface so it could be swapped for an
API-based embedding provider (OpenAI, Cohere, etc) without touching any
other module.
"""
from functools import lru_cache
from typing import List

from app.config import settings


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]
