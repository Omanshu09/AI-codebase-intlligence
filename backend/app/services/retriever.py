from typing import List, Dict, Any

from app.config import settings
from app.services import embeddings, vector_db


def retrieve(repository_id: str, question: str, top_k: int = None) -> List[Dict[str, Any]]:
    """
    Embeds the question and runs a similarity search against the
    repository's vector collection. Returns a list of dicts with the
    chunk content, metadata, and a similarity score (higher = closer).
    """
    top_k = top_k or settings.top_k
    query_vector = embeddings.embed_text(question)
    results = vector_db.query(repository_id, query_vector, top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    hits = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        # Chroma returns a distance (lower = more similar) for cosine space
        # in [0, 2]; convert to an intuitive 0-1 "similarity" score.
        score = max(0.0, 1 - (dist / 2))
        hits.append({
            "content": doc,
            "file_path": meta.get("file_path"),
            "symbol": meta.get("symbol"),
            "start_line": meta.get("start_line"),
            "end_line": meta.get("end_line"),
            "language": meta.get("language"),
            "score": round(score, 4),
        })
    return hits
