# Novel Writing Agent

AI-powered Chinese web novel auto-writing system with full lifecycle management — from world building and character design to serialized chapter generation with quality review.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, Radix UI |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Celery |
| AI | LangChain, OpenAI GPT-4o, text-embedding-3-small |
| Database | PostgreSQL 16 + pgvector (IVFFlat + cosine similarity) |
| Cache / Queue | Redis (Celery broker, pub/sub for SSE) |
| MCP | Self-built MCP Server (8 tools, 3 resources, 2 prompts) |
| Deployment | Docker Compose (6 services) |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Setup

```bash
# 1. Clone and enter the project
cd agent

# 2. Set your OpenAI API key
cp .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-your-key

# 3. Start all services
docker compose up -d

# 4. Run database migrations
docker compose exec backend alembic upgrade head

# 5. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 3000 | Next.js web UI |
| `backend` | 8000 | FastAPI REST API + SSE streaming |
| `worker` | — | Celery async task worker (chapter/outline generation) |
| `beat` | — | Celery Beat scheduler (auto-generation trigger) |
| `db` | 5432 | PostgreSQL 16 + pgvector |
| `redis` | 6379 | Redis (broker, pub/sub, scheduler persistence) |

## Features

### Novel Lifecycle Management
- Create novels with genre, synopsis, and custom style configuration
- Configure tone, POV, words-per-chapter, and custom writing instructions
- Track progress with chapter count and publish status

### World & Character Workshop
- Design world settings with categories (regions, factions, power systems)
- Create character profiles with roles, descriptions, and structured attributes
- All settings are vector-embedded for AI context retrieval

### Outline Planning
- Hierarchical outline tree: volume → arc → chapter
- Drag-and-drop reordering with parent-child relationships
- AI-powered outline generation at any level

### AI Chapter Generation
- 4-stage segmented generation: opening → development → climax → ending
- Real-time SSE streaming preview as content is generated
- Manual trigger with configurable word count per chapter
- Context-aware: injects outline, character profiles, and RAG knowledge

### Review & Publish Workflow
- 5-dimension AI quality review: plot coherence, character consistency, pacing, prose quality, dialogue
- Side-by-side review desk with approve / rewrite actions
- Draft → Review → Published status pipeline

### RAG Knowledge Base
- Upload reference documents (world lore, writing guidelines, style references)
- Automatic chunking with Chinese-aware text splitting
- Hybrid search: vector similarity (cosine) + keyword (ILIKE) → RRF fusion
- Retrieved context injected into generation prompts

### Scheduled Auto-Generation
- Optional cron-based scheduling per novel
- Celery Beat scans every 5 minutes for due chapters
- Queue management with task history and status tracking

## Project Structure

```
agent/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── docs/
│   └── superpowers/
│       ├── specs/          # Design documents
│       └── plans/          # Implementation plans
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test suite
│   └── app/
│       ├── main.py         # FastAPI application
│       ├── config.py       # Pydantic settings
│       ├── api/
│       │   ├── deps.py     # Auth + DB session dependency
│       │   └── v1/         # REST API routes (7 modules)
│       ├── models/         # SQLAlchemy models (6 entities)
│       ├── schemas/        # Pydantic request/response schemas
│       ├── services/       # Business logic layer
│       ├── ai/
│       │   ├── agents/     # OutlineAgent, WritingAgent, ReviewAgent
│       │   ├── prompts/    # Prompt templates (outline, writing, review)
│       │   └── rag/        # Splitter, embedder, retriever
│       ├── mcp/
│       │   ├── server.py   # MCP Server definition
│       │   ├── tools/      # 8 MCP tools (generation, query, knowledge, consistency)
│       │   ├── resources/  # 3 MCP resources (outline, characters, style)
│       │   └── prompts/    # 2 MCP prompts (continue_writing, character_dialogue)
│       ├── tasks/
│       │   ├── celery_app.py           # Celery configuration
│       │   └── generation_tasks.py     # Async generation tasks
│       └── utils/
│           └── logging.py  # Structured logging (structlog)
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.ts
    ├── next.config.js
    └── src/
        ├── app/            # Next.js App Router pages
        │   ├── page.tsx                    # Dashboard
        │   ├── projects/                   # Novel list + create
        │   └── projects/[id]/              # Workspace (settings, chapters, review, generation)
        ├── components/
        │   ├── ui/         # shadcn-style components (Button, Card, Badge, Dialog, Tabs)
        │   └── layout/     # Sidebar navigation
        ├── lib/
        │   ├── api.ts      # Full API client
        │   └── utils.ts    # cn() helper
        └── types/
            └── index.ts    # TypeScript interfaces
```

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/novels` | List all novels |
| POST | `/api/v1/novels` | Create a novel |
| GET | `/api/v1/novels/{id}` | Get novel detail |
| PATCH | `/api/v1/novels/{id}` | Update novel |
| DELETE | `/api/v1/novels/{id}` | Delete novel |
| PATCH | `/api/v1/novels/{id}/style` | Update writing style |
| GET | `/api/v1/novels/{id}/chapters` | List chapters |
| GET | `/api/v1/chapters/{id}` | Get chapter |
| PATCH | `/api/v1/chapters/{id}` | Update chapter |
| POST | `/api/v1/chapters/{id}/publish` | Publish chapter |
| GET/POST | `/api/v1/characters` | List / Create characters |
| GET/POST | `/api/v1/world-settings` | List / Create world settings |
| GET | `/api/v1/novels/{id}/outlines` | Get outline tree |
| POST | `/api/v1/outlines` | Create outline node |
| PATCH | `/api/v1/outlines/{id}` | Update outline |
| DELETE | `/api/v1/outlines/{id}` | Delete outline |
| PATCH | `/api/v1/outlines/{id}/reorder` | Reorder outline |
| POST | `/api/v1/generation/outline` | Trigger outline generation |
| POST | `/api/v1/generation/chapter` | Trigger chapter generation |
| GET | `/api/v1/generation/tasks` | List generation tasks |
| GET | `/api/v1/generation/stream/{task_id}` | SSE stream |
| POST | `/api/v1/rag/upload` | Upload RAG document |
| GET | `/api/v1/rag/documents` | List RAG documents |
| POST | `/api/v1/rag/search` | Hybrid search |
| GET | `/health` | Health check (DB + Redis) |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4o` | Model for generation |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Model for embeddings |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection string |
| `ACCESS_TOKEN` | `change-me` | Bearer token (dev mode when `change-me`) |

## Testing

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
