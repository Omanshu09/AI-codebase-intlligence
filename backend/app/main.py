from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import init_db
from app.api import health, repositories, query

app = FastAPI(
    title="AI Codebase Intelligence Platform",
    description="Ingests GitHub repositories and answers natural-language questions about the code via a RAG pipeline.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(repositories.router)
app.include_router(query.router)


@app.on_event("startup")
def on_startup():
    init_db()
