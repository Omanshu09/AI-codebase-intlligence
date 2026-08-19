import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Repository, Query as QueryModel
from app.schemas.query import QueryRequest, QueryResponse, SourceChunk
from app.services import retriever, llm

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
def ask_question(payload: QueryRequest, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == payload.repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=409, detail=f"Repository is not ready (status: {repo.status})")

    hits = retriever.retrieve(repo.id, payload.question, payload.top_k)
    answer = llm.generate_answer(payload.question, hits)

    sources = [
        SourceChunk(
            file_path=h["file_path"], symbol=h.get("symbol") or None,
            start_line=h.get("start_line"), end_line=h.get("end_line"),
            snippet=h["content"][:600], score=h["score"],
        ) for h in hits
    ]

    record = QueryModel(
        repository_id=repo.id, question=payload.question, answer=answer,
        sources=json.dumps([s.model_dump() for s in sources]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return QueryResponse(
        id=record.id, question=record.question, answer=record.answer,
        sources=sources, created_at=record.created_at,
    )
