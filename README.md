# AI Codebase Intelligence Platform

Ingests a public GitHub repository, parses and chunks its source code along
function/class boundaries, embeds each chunk, and lets you ask natural
language questions about the codebase through a RAG (Retrieval-Augmented
Generation) pipeline — with source-cited answers.

Runs **entirely for free** by default: embeddings run locally via
`fastembed` (ONNX Runtime, no PyTorch -- important on memory-capped hosts
like a free-tier Render instance), the vector index is local (`ChromaDB`,
disk-based, no server), and metadata is stored in SQLite. Add an
`ANTHROPIC_API_KEY` if you want real LLM-generated explanations instead of
the templated fallback answer.

> **Deploying on a free/memory-limited host?** This originally used
> `sentence-transformers`, which pulls in PyTorch (~700MB runtime). On a
> 512MB instance that got OOM-killed the instant the model actually loaded
> -- ingestion or a query would just hang forever with no visible error,
> the classic symptom of a process dying mid-request. Switched to
> `fastembed` for exactly this reason.

## Architecture

```
GitHub Repo URL
      |
      v
 Clone (GitPython)
      |
      v
 File Scanner (walks repo, filters by extension/size)
      |
      v
 Code Parser (Python: ast module | others: regex heuristics)
      |
      v
 Chunker (splits along function/class boundaries)
      |
      v
 Embedding Model (sentence-transformers, local, free)
      |
      v
 Vector DB (ChromaDB, one collection per repo)
      |
      |         User Question
      |               |
      |               v
      |        Query Embedding
      |               |
      +------> Vector Similarity Search
                       |
                       v
              Top-K Relevant Chunks
                       |
                       v
              Context Builder + LLM
              (Claude if API key set,
               else templated fallback)
                       |
                       v
              Answer + Cited Sources
```

## Project layout

```
ai-codebase-intelligence/
├── backend/
│   └── app/
│       ├── main.py                # FastAPI app, CORS, router registration
│       ├── config.py              # env-driven settings
│       ├── api/
│       │   ├── health.py          # GET  /health
│       │   ├── repositories.py    # POST /repositories/ingest, GET/DELETE
│       │   └── query.py           # POST /query  (the RAG endpoint)
│       ├── services/
│       │   ├── github_service.py  # clone/cleanup repos
│       │   ├── parser.py          # AST (Python) + regex (other langs)
│       │   ├── chunker.py         # symbol-aware chunking
│       │   ├── embeddings.py      # sentence-transformers wrapper
│       │   ├── vector_db.py       # ChromaDB wrapper
│       │   ├── retriever.py       # question -> top-K chunks
│       │   ├── llm.py             # chunks -> natural language answer
│       │   └── ingestion.py       # orchestrates the full pipeline
│       ├── database/              # SQLAlchemy engine, models
│       └── schemas/               # Pydantic request/response models
├── frontend/                      # React + Vite chat UI
├── docker-compose.yml             # backend + frontend + postgres
└── README.md
```

## Run locally (no Docker, fastest way to try it)

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
The API is now at `http://localhost:8000` — interactive docs at
`http://localhost:8000/docs`. The first request downloads the local
embedding model (~90MB) from Hugging Face, cached afterward.

**Frontend** (separate terminal)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`, paste a public GitHub repo URL, click
**Analyze Repository**, then ask questions once its status shows `ready`.

## Run with Docker (backend + frontend + Postgres)

```bash
# optional, for real LLM answers instead of the free fallback:
export ANTHROPIC_API_KEY=sk-ant-...

docker compose up --build
```
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/docs`
- Postgres: `localhost:5432` (user/pass/db: `codebase`)

Note: the frontend Docker image is a static build, so `VITE_API_URL` is
baked in at build time — if you change the backend URL, rebuild the
frontend image (`docker compose build frontend`).

## API reference

| Method | Path                        | Description                          |
|--------|-----------------------------|---------------------------------------|
| POST   | `/repositories/ingest`      | `{ "repo_url": "..." }` — clones, parses, embeds, indexes |
| GET    | `/repositories`             | List all indexed repositories        |
| GET    | `/repositories/{id}`        | Get one repository's status/stats    |
| DELETE | `/repositories/{id}`        | Remove a repository and its vectors  |
| POST   | `/query`                    | `{ "repository_id", "question" }` — returns answer + cited sources |
| GET    | `/health`                   | Liveness check                       |

## Why it's built this way (for your resume / interviews)

- **RAG instead of dumping the whole repo into the LLM** — keeps context
  small, relevant, and within token limits regardless of repo size.
- **Symbol-aware chunking** (`parser.py` + `chunker.py`) — splitting on
  function/class boundaries instead of raw character counts keeps each
  chunk semantically complete, which measurably improves retrieval quality
  over naive fixed-size splitting.
- **Metadata alongside vectors** — every chunk stores `file_path`, `symbol`,
  `start_line`/`end_line` so answers can cite exact locations, not just
  raw text.
- **Postgres for app metadata, Chroma for vectors** — a common production
  pattern: relational data (repos, files, query history) doesn't belong in
  a vector store, and vice versa.
- **Pluggable embedding/LLM layers** — `embeddings.py` and `llm.py` are
  thin wrappers so swapping the local model for an API-based one (OpenAI,
  Cohere) or a different LLM provider touches one file, not the pipeline.

### Questions you should be able to answer about this project
1. Why RAG instead of sending the whole repo to the LLM?
2. What is an embedding, concretely?
3. Why a vector database instead of a SQL `LIKE` search?
4. How is source code split into chunks, and why symbol-aware over fixed-size?
5. What metadata travels alongside each vector, and why?
6. How does similarity search / Top-K retrieval work?
7. Why Postgres in addition to the vector DB?
8. How would you scale ingestion for a 50,000-file monorepo? (background
   job queue instead of synchronous ingestion; chunked/streamed embedding
   batches; incremental re-indexing on git diff instead of full re-clone.)
9. What's the current parsing limitation, and how would you fix it?
   (Python uses the real `ast` module; every other language uses regex
   heuristics — swapping in `tree-sitter` would give AST-level accuracy
   for all languages.)
10. How is this different from a bare "call the OpenAI API" wrapper?
    (Ingestion, parsing, chunking, embeddings, vector search, and citation
    are all real engineering, not just one API call.)

## Known limitations / good next steps to mention in interviews
- Non-Python parsing is regex-based, not a true AST — swap in `tree-sitter`
  for multi-language parsing accuracy.
- Ingestion runs synchronously in the request; for large repos, move it to
  a background task queue (Celery/RQ) with a polling `status` endpoint.
- No auth — add API keys / OAuth before exposing this publicly.
- No incremental re-indexing — re-ingesting always re-clones and re-embeds
  the whole repo; a production version would diff against the last commit.
