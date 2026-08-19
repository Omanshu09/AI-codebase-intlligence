"""
Thin wrapper around ChromaDB, used as the vector database for semantic
code search. Chroma persists to disk (settings.chroma_persist_dir) so
no separate server or paid service is required. One collection per
repository keeps searches scoped and makes deleting a repo trivial.
"""
from functools import lru_cache
from typing import List, Dict, Any

import chromadb

from app.config import settings


@lru_cache(maxsize=1)
def _client():
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def _collection_name(repository_id: str) -> str:
    return f"repo_{repository_id}"


def get_or_create_collection(repository_id: str):
    return _client().get_or_create_collection(name=_collection_name(repository_id))


def add_chunks(repository_id: str, ids: List[str], embeddings: List[List[float]],
               documents: List[str], metadatas: List[Dict[str, Any]]) -> None:
    if not ids:
        return
    collection = get_or_create_collection(repository_id)
    # Chroma has a practical batch-size limit; write in slices to be safe.
    batch = 500
    for i in range(0, len(ids), batch):
        collection.add(
            ids=ids[i:i + batch],
            embeddings=embeddings[i:i + batch],
            documents=documents[i:i + batch],
            metadatas=metadatas[i:i + batch],
        )


def query(repository_id: str, query_embedding: List[float], top_k: int) -> Dict[str, Any]:
    collection = get_or_create_collection(repository_id)
    if collection.count() == 0:
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
    return collection.query(query_embeddings=[query_embedding], n_results=top_k)


def delete_collection(repository_id: str) -> None:
    try:
        _client().delete_collection(name=_collection_name(repository_id))
    except Exception:
        pass
