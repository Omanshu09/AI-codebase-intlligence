"""
Converts text (code chunks or user questions) into vector embeddings.

Runs 100% locally via `fastembed` -- no API key, no cost, and critically
no PyTorch. fastembed uses ONNX Runtime with a small quantized model, which
uses a small fraction of the memory that sentence-transformers + PyTorch
does. That matters a lot on memory-capped hosts (e.g. a 512MB free-tier
Render instance): the PyTorch-based version was getting OOM-killed the
moment the model actually loaded, which is why ingestion/queries would
hang forever with no error. This module is a thin wrapper so the embedding
backend could still be swapped again (an API-based provider, etc) without
touching any other module.
"""
from functools import lru_cache
from typing import List

from app.config import settings


@lru_cache(maxsize=1)
def _get_model():
    from fastembed import TextEmbedding
    return TextEmbedding(model_name=settings.embedding_model)


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    model = _get_model()
    vectors = list(model.embed(texts))
    return [v.tolist() for v in vectors]


def embed_text(text: str) -> List[float]:
    return embed_texts([text])[0]
