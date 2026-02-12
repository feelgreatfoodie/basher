# CLU API

Multi-transcript analysis and synthesis microservice. Part of the [CLU](../docs/CLU-GUIDE.md) ecosystem.

## Quick Start

```bash
# Start API + PostgreSQL
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Seed sample data (optional)
docker-compose exec api python scripts/seed.py
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects` | List projects |
| GET | `/api/v1/projects/{id}` | Get project |
| POST | `/api/v1/projects/{id}/transcripts` | Upload transcript (multipart) |
| GET | `/api/v1/projects/{id}/transcripts` | List transcripts |
| POST | `/api/v1/projects/{id}/analyze` | Trigger analysis (background) |
| GET | `/api/v1/projects/{id}/analysis/status` | Poll analysis status |
| GET | `/api/v1/projects/{id}/analysis/results` | Get full results |
| GET | `/api/v1/projects/{id}/analysis/{type}` | Get specific result section |
| POST | `/api/v1/projects/{id}/prd` | Generate PRD from analysis |

### Result types

`summary`, `conflicts`, `gaps`, `decisions`, `requirements`, `stakeholders`, `action-items`

## Architecture

```
app/
├── api/          # FastAPI route handlers
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic request/response models
├── services/     # Business logic (extraction, synthesis, PRD generation)
└── prompts/      # Prompt templates for Anthropic SDK
```

### Pipeline

1. **Upload** transcripts to a project
2. **Trigger analysis** — spawns a background job
3. **Extraction** (Phase 1) — each transcript extracted concurrently via Claude Sonnet
4. **Synthesis** (Phase 2) — all extractions cross-referenced via Claude Opus
5. **PRD** (Phase 3, optional) — analysis converted to Basher-compatible PRD

Concurrency is controlled by `MAX_CONCURRENT_EXTRACTIONS` (default: 3).

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://clu:clu_dev@localhost:5432/clu` | PostgreSQL connection |
| `ANTHROPIC_API_KEY` | (required) | Anthropic API key |
| `EXTRACTION_MODEL` | `claude-sonnet-4-5-20250929` | Model for extraction |
| `SYNTHESIS_MODEL` | `claude-opus-4-6` | Model for synthesis |
| `MAX_CONCURRENT_EXTRACTIONS` | `3` | Max parallel extraction workers |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (uses SQLite in-memory, no Docker needed)
pytest

# Lint
ruff check app/ tests/
```

## Tech Stack

- **FastAPI** — async API framework
- **SQLAlchemy 2.0** — ORM with mapped_column syntax
- **PostgreSQL 16** — persistence
- **Alembic** — database migrations
- **Anthropic SDK** — direct Claude API calls (no LangChain)
- **Docker** — containerization
