import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database.db import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending | processing | ready | failed
    file_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    files = relationship("RepoFile", back_populates="repository", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="repository", cascade="all, delete-orphan")


class RepoFile(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, default=gen_id)
    repository_id = Column(String, ForeignKey("repositories.id"))
    path = Column(String, nullable=False)
    language = Column(String, nullable=True)
    size = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)

    repository = relationship("Repository", back_populates="files")


class Query(Base):
    __tablename__ = "queries"

    id = Column(String, primary_key=True, default=gen_id)
    repository_id = Column(String, ForeignKey("repositories.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    sources = Column(Text, nullable=True)  # JSON-encoded list of source refs
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="queries")
