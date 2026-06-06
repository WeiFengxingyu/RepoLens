# RepoLens

RepoLens is a repository-level Code Agent platform for codebase understanding and PR review.

Current phase: **Phase 0 - engineering skeleton**.

## Architecture

- Frontend: Next.js + TypeScript
- Backend: Python + FastAPI
- Agent orchestration: LangGraph
- Metadata database: SQLite
- Vector database: Qdrant
- Code graph: NetworkX
- Keyword retrieval: BM25
- Deployment: Docker Compose

## Phase 0 Scope

Phase 0 only initializes the project foundation:

- monorepo directory structure
- FastAPI backend skeleton
- Next.js workbench skeleton
- configuration module
- SQLite session setup
- health/status endpoints
- Docker Compose draft
- development process log

Business features such as repository import, parsing, indexing, retrieval, QA, and PR Review start from later phases.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Docker Compose:

```bash
docker compose up --build
```

Default URLs:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8000/health
- Backend status: http://localhost:8000/api/status
- Qdrant: http://localhost:6333

## Documentation

- Requirements: `docs/requirements-analysis.md`
- Outline design: `docs/outline-design.md`
- P0+ development plan: `docs/p0-plus-development-plan.md`
- Development process log: `docs/development-worklog.md`

