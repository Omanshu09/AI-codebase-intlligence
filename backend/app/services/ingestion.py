import os
import uuid

from sqlalchemy.orm import Session

from app.config import settings
from app.database.models import Repository, RepoFile
from app.services import github_service, embeddings, vector_db
from app.services.chunker import chunk_file, _language_for


def _repo_name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1].removesuffix(".git")


def _iter_source_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in settings.ignored_dirs and not d.startswith(".")]
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            if not filename.endswith(settings.supported_extensions):
                continue
            try:
                if os.path.getsize(full_path) > settings.max_file_size_bytes:
                    continue
            except OSError:
                continue
            yield full_path


def ingest_repository(db: Session, repo_url: str) -> Repository:
    """
    Runs the full pipeline for one repository:
      clone -> walk files -> parse -> chunk -> embed -> store in
      Chroma (vectors) and Postgres/SQLite (metadata).

    Synchronous by design for portfolio-project simplicity. For large
    repositories in production you'd move this onto a background task
    queue (Celery/RQ) and poll `status` from the client instead.
    """
    repo = Repository(name=_repo_name_from_url(repo_url), url=repo_url, status="processing")
    db.add(repo)
    db.commit()
    db.refresh(repo)

    try:
        local_path = github_service.clone_repository(repo_url, repo.id)

        total_chunks = 0
        file_count = 0

        for file_path in _iter_source_files(local_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    source = fh.read()
            except OSError:
                continue
            if not source.strip():
                continue

            rel_path = os.path.relpath(file_path, local_path)
            chunks = chunk_file(rel_path, source)
            if not chunks:
                continue

            texts = [c.content for c in chunks]
            vectors = embeddings.embed_texts(texts)
            ids = [f"{repo.id}:{uuid.uuid4().hex}" for _ in chunks]
            metadatas = [{
                "file_path": c.file_path,
                "language": c.language,
                "symbol": c.symbol or "",
                "kind": c.kind,
                "start_line": c.start_line,
                "end_line": c.end_line,
            } for c in chunks]

            vector_db.add_chunks(repo.id, ids, vectors, texts, metadatas)

            db.add(RepoFile(
                repository_id=repo.id, path=rel_path,
                language=_language_for(rel_path),
                size=len(source), chunk_count=len(chunks),
            ))

            total_chunks += len(chunks)
            file_count += 1

        repo.status = "ready"
        repo.file_count = file_count
        repo.chunk_count = total_chunks
        db.commit()
        db.refresh(repo)

    except Exception as exc:  # noqa: BLE001 -- surface any failure on the record
        repo.status = "failed"
        repo.error_message = str(exc)[:2000]
        db.commit()
        db.refresh(repo)
    finally:
        github_service.cleanup_repository(os.path.join(settings.clone_dir, repo.id))

    return repo


def delete_repository(db: Session, repo: Repository) -> None:
    vector_db.delete_collection(repo.id)
    db.delete(repo)
    db.commit()
