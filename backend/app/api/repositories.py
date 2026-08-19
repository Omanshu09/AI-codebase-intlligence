from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.database.models import Repository
from app.schemas.repository import RepositoryIngestRequest, RepositoryOut
from app.services import ingestion

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/ingest", response_model=RepositoryOut)
def ingest(payload: RepositoryIngestRequest, db: Session = Depends(get_db)):
    if not payload.repo_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="repo_url must be a valid http(s) GitHub URL")
    repo = ingestion.ingest_repository(db, payload.repo_url)
    if repo.status == "failed":
        raise HTTPException(status_code=422, detail=f"Ingestion failed: {repo.error_message}")
    return repo


@router.get("", response_model=list[RepositoryOut])
def list_repositories(db: Session = Depends(get_db)):
    return db.query(Repository).order_by(Repository.created_at.desc()).all()


@router.get("/{repository_id}", response_model=RepositoryOut)
def get_repository(repository_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repository_id}")
def delete_repository(repository_id: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    ingestion.delete_repository(db, repo)
    return {"deleted": True, "id": repository_id}
