"""
Turns (question + retrieved code chunks) into a natural-language answer.

If ANTHROPIC_API_KEY is set, this calls Claude for a real generated
explanation. If not, the app still works end-to-end for free: it
returns a templated summary built directly from the retrieved chunks,
so ingestion, retrieval and the UI can all be demoed with zero API cost.
Swap this module out (or point it at another provider) without touching
any other part of the pipeline.
"""
from typing import List, Dict, Any

from app.config import settings

SYSTEM_PROMPT = (
    "You are an AI codebase assistant. Answer the user's question using ONLY "
    "the provided repository context below. Reference specific files and "
    "functions by name. If the context doesn't contain enough information, "
    "say so plainly instead of guessing."
)


def _build_context(chunks: List[Dict[str, Any]]) -> str:
    parts = []
    for c in chunks:
        header = f"File: {c['file_path']}"
        if c.get("symbol"):
            header += f" | {c.get('kind', 'symbol')}: {c['symbol']}"
        header += f" | lines {c.get('start_line')}-{c.get('end_line')}"
        parts.append(f"{header}\n{c['content']}")
    return "\n\n---\n\n".join(parts)


def _fallback_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return (
            "I couldn't find any indexed code relevant to that question. "
            "Try re-ingesting the repository or rephrasing the question."
        )
    top = chunks[0]
    lead = f"The most relevant match for \"{question}\" is "
    if top.get("symbol"):
        lead += f"`{top['symbol']}` in `{top['file_path']}` (lines {top['start_line']}-{top['end_line']})."
    else:
        lead += f"`{top['file_path']}` (lines {top['start_line']}-{top['end_line']})."
    others = ", ".join(sorted({c["file_path"] for c in chunks[1:]})) or "none"
    return (
        f"{lead} Set ANTHROPIC_API_KEY in your .env for a full generated "
        f"explanation -- for now, here are the raw matches (see Sources "
        f"below). Other related files: {others}."
    )


def generate_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
    if not settings.anthropic_api_key:
        return _fallback_answer(question, chunks)

    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    context = _build_context(chunks)
    user_message = f"Question:\n{question}\n\nRepository Context:\n{context}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    return "\n".join(text_blocks) if text_blocks else _fallback_answer(question, chunks)
