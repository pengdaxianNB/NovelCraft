# 自动写小说 Agent 实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从零搭建一个基于 AI 的中文网文自动写作系统，支持世界观/角色设定、大纲规划、章节生成、人工审核、RAG 知识库增强，Docker 一键部署。

**Architecture:** FastAPI 单体后端 + Celery 异步任务 + 自建 MCP Server（AI 工具中间层）+ LangChain 三 Agent 协作（大纲/写作/审校）+ Next.js 前端 + PostgreSQL/pgvector + Redis，全部 Docker Compose 编排。

**Tech Stack:** Python 3.12 + FastAPI + Celery + LangChain + OpenAI + MCP SDK + PostgreSQL 16 + pgvector + Redis 7 + Next.js 14 + shadcn/ui + Tailwind CSS + Docker

---

## Chunk 1: 项目脚手架与基础设施

### Task 1.1: 根目录配置文件

**Files:**
- Create: `.env.example`
- Create: `docker-compose.yml`
- Create: `.gitignore`

- [ ] **Step 1: 创建 .env.example**

```bash
cat > .env.example << 'EOF'
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Auth
ACCESS_TOKEN=change-me-to-a-random-string

# Database
POSTGRES_USER=novel_user
POSTGRES_PASSWORD=novel_pass
POSTGRES_DB=novel_agent
DATABASE_URL=postgresql://novel_user:novel_pass@db:5432/novel_agent

# Redis
REDIS_URL=redis://redis:6379/0
EOF
```

- [ ] **Step 2: 创建 docker-compose.yml**

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-novel_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-novel_pass}
      POSTGRES_DB: ${POSTGRES_DB:-novel_agent}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-novel_user}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL}
      - OPENAI_EMBEDDING_MODEL=${OPENAI_EMBEDDING_MODEL}
      - ACCESS_TOKEN=${ACCESS_TOKEN}
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  worker:
    build: ./backend
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=1
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL}
      - OPENAI_EMBEDDING_MODEL=${OPENAI_EMBEDDING_MODEL}
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  beat:
    build: ./backend
    command: celery -A app.tasks.celery_app beat --loglevel=info --scheduler celery_beat_redis.scheduler:RedisScheduler
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend

volumes:
  pgdata:
```

- [ ] **Step 3: 创建 .gitignore**

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
*.egg

# Node
node_modules/
.next/
out/

# Environment
.env
*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
pgdata/

# Coverage
htmlcov/
.coverage
```

- [ ] **Step 4: 提交**

```bash
git add .env.example docker-compose.yml .gitignore
git commit -m "chore: add project scaffolding with Docker Compose"
```

### Task 1.2: 后端项目初始化

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/logging.py`

- [ ] **Step 1: 创建 backend/Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .
```

- [ ] **Step 2: 创建 backend/pyproject.toml**

```toml
[project]
name = "novel-agent"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "pgvector>=0.3.0",
    "psycopg2-binary>=2.9.9",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "celery[redis]>=5.4.0",
    "celery-beat-redis>=0.0.2",
    "redis>=5.0.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-mcp-adapters>=0.1.0",
    "mcp>=1.0.0",
    "openai>=1.50.0",
    "tenacity>=9.0.0",
    "structlog>=24.0.0",
    "python-multipart>=0.0.9",
    "sse-starlette>=2.0.0",
    "httpx>=0.27.0",
    "alembic-postgresql>=0.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.0",
    "ruff>=0.5.0",
]

[build-system]
requires = ["setuptools>=75.0.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 3: 创建 backend/app/config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://novel_user:novel_pass@localhost:5432/novel_agent"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Auth
    access_token: str = "change-me"

    # App
    app_name: str = "Novel Writing Agent"
    debug: bool = False

    @property
    def openai_api_keys(self) -> list[str]:
        return [k.strip() for k in self.openai_api_key.split(",") if k.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
```

- [ ] **Step 4: 创建 backend/app/utils/logging.py**

```python
import structlog
import uuid
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer() if __import__("app.config").config.settings.debug
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str | None = None) -> structlog.BoundLogger:
    return structlog.get_logger(name or __name__)

def set_trace_id() -> str:
    trace_id = uuid.uuid4().hex[:12]
    trace_id_var.set(trace_id)
    return trace_id

def get_trace_id() -> str:
    return trace_id_var.get()
```

- [ ] **Step 5: 创建 backend/app/main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.app_name}
```

- [ ] **Step 6: 提交**

```bash
git add backend/
git commit -m "chore: init FastAPI backend with config and logging"
```

### Task 1.3: Next.js 前端项目初始化

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/next.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/app/layout.tsx`
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/app/globals.css`

- [ ] **Step 1: 创建 frontend/Dockerfile**

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

CMD ["npm", "run", "dev"]
```

- [ ] **Step 2: 创建 frontend/package.json**

```json
{
  "name": "novel-agent-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-label": "^2.1.0",
    "@radix-ui/react-select": "^2.1.0",
    "@radix-ui/react-separator": "^1.1.0",
    "@radix-ui/react-slot": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.0",
    "@radix-ui/react-toast": "^1.2.0",
    "@radix-ui/react-tooltip": "^1.1.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.400.0",
    "tailwind-merge": "^2.4.0",
    "tailwindcss-animate": "^1.0.7"
  },
  "devDependencies": {
    "@types/node": "^20.14.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0"
  }
}
```

- [ ] **Step 3: 创建 frontend/next.config.js**

```js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
};

module.exports = nextConfig;
```

- [ ] **Step 4: 创建 frontend/tailwind.config.ts**

```ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

- [ ] **Step 5: 创建 frontend/src/app/globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --border: 214.3 31.8% 91.4%;
  }
}
```

- [ ] **Step 6: 创建 frontend/src/app/layout.tsx**

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Novel Writing Agent",
  description: "AI-powered Chinese web novel writing system",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

- [ ] **Step 7: 创建 frontend/src/app/page.tsx（占位仪表盘）**

```tsx
export default function Dashboard() {
  return (
    <main className="min-h-screen bg-background p-8">
      <h1 className="text-3xl font-bold text-foreground">Novel Writing Agent</h1>
      <p className="mt-4 text-muted-foreground">AI 驱动的网文写作系统</p>
    </main>
  );
}
```

- [ ] **Step 8: 提交**

```bash
git add frontend/
git commit -m "chore: init Next.js frontend with Tailwind CSS"
```

---

## Chunk 2: 数据库层

### Task 2.1: SQLAlchemy 模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/novel.py`
- Create: `backend/app/models/character.py`
- Create: `backend/app/models/world_setting.py`
- Create: `backend/app/models/outline.py`
- Create: `backend/app/models/chapter.py`
- Create: `backend/app/models/rag.py`
- Create: `backend/app/models/generation_task.py`
- Create: `backend/app/models/base.py`

- [ ] **Step 1: 创建 backend/app/models/base.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
```

- [ ] **Step 2: 创建 backend/app/models/novel.py**

```python
from sqlalchemy import String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, new_uuid


class Novel(Base, TimestampMixin):
    __tablename__ = "novels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    genre: Mapped[str] = mapped_column(String(50), nullable=False, default="玄幻")
    synopsis: Mapped[str | None] = mapped_column(Text)
    style_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    schedule_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="planning")

    characters = relationship("Character", back_populates="novel", cascade="all, delete-orphan")
    world_settings = relationship("WorldSetting", back_populates="novel", cascade="all, delete-orphan")
    outlines = relationship("Outline", back_populates="novel", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="novel", cascade="all, delete-orphan")
```

- [ ] **Step 3: 创建 backend/app/models/character.py**

```python
import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin, new_uuid


class Character(Base, TimestampMixin):
    __tablename__ = "characters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="配角")
    profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    novel = relationship("Novel", back_populates="characters")
```

- [ ] **Step 4: 创建 backend/app/models/world_setting.py**

```python
import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin, new_uuid


class WorldSetting(Base, TimestampMixin):
    __tablename__ = "world_settings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    novel = relationship("Novel", back_populates="world_settings")
```

- [ ] **Step 5: 创建 backend/app/models/outline.py**

```python
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, new_uuid


class Outline(Base, TimestampMixin):
    __tablename__ = "outlines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id"), nullable=False)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # volume/arc/chapter
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("outlines.id"), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="planned")

    novel = relationship("Novel", back_populates="outlines")
    children = relationship("Outline", backref="parent", remote_side=[id], cascade="all, delete-orphan")
```

- [ ] **Step 6: 创建 backend/app/models/chapter.py**

```python
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin, new_uuid


class Chapter(Base, TimestampMixin):
    __tablename__ = "chapters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id"), nullable=False)
    outline_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("outlines.id"), nullable=True)
    chapter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    generation_meta: Mapped[dict] = mapped_column(JSONB, default=dict)

    novel = relationship("Novel", back_populates="chapters")
```

- [ ] **Step 7: 创建 backend/app/models/rag.py**

```python
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.models.base import Base, TimestampMixin, new_uuid


class RagDocument(Base, TimestampMixin):
    __tablename__ = "rag_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id"), nullable=False)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="processing")


class RagChunk(Base, TimestampMixin):
    __tablename__ = "rag_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rag_documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
```

- [ ] **Step 8: 创建 backend/app/models/generation_task.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, new_uuid


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)
    novel_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("novels.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    progress: Mapped[dict] = mapped_column(JSONB, default=dict)
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 9: 提交**

```bash
git add backend/app/models/
git commit -m "feat: add SQLAlchemy models for all entities"
```

### Task 2.2: Alembic 迁移配置

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

- [ ] **Step 1: 初始化 Alembic 并配置**

在 backend 目录中运行 `alembic init alembic`，然后修改 `alembic/env.py`：

```python
from app.config import settings
from app.models.base import Base
from app.models.novel import Novel
from app.models.character import Character
from app.models.world_setting import WorldSetting
from app.models.outline import Outline
from app.models.chapter import Chapter
from app.models.rag import RagDocument, RagChunk
from app.models.generation_task import GenerationTask

target_metadata = Base.metadata

def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url
    connectable = engine_from_config(configuration, prefix="sqlalchemy.")
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

- [ ] **Step 2: 生成初始迁移**

```bash
cd backend && alembic revision --autogenerate -m "init" && cd ..
```

- [ ] **Step 3: 提交**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add Alembic migrations"
```

---

## Chunk 3: 后端核心层

### Task 3.1: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/novel.py`
- Create: `backend/app/schemas/character.py`
- Create: `backend/app/schemas/world_setting.py`
- Create: `backend/app/schemas/outline.py`
- Create: `backend/app/schemas/chapter.py`
- Create: `backend/app/schemas/rag.py`
- Create: `backend/app/schemas/generation.py`
- Create: `backend/app/schemas/common.py`

- [ ] **Step 1: 创建 common.py**

```python
from pydantic import BaseModel
from datetime import datetime

class BaseResponse(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
```

- [ ] **Step 2: 创建 novel.py**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any

class StyleConfig(BaseModel):
    tone: str = "热血"
    pov: str = "第三人称"
    words_per_chapter: int = 3000
    custom_instructions: str = ""

class ScheduleConfig(BaseModel):
    enabled: bool = False
    cron: str = "0 */6 * * *"

class NovelCreate(BaseModel):
    title: str = Field(..., max_length=200)
    genre: str = Field(default="玄幻", max_length=50)
    synopsis: str | None = None
    style_config: StyleConfig = StyleConfig()
    schedule_config: ScheduleConfig = ScheduleConfig()

class NovelUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    genre: str | None = Field(None, max_length=50)
    synopsis: str | None = None
    status: str | None = None

class NovelStyleUpdate(BaseModel):
    tone: str | None = None
    pov: str | None = None
    words_per_chapter: int | None = None
    custom_instructions: str | None = None

class NovelResponse(BaseModel):
    id: str
    title: str
    genre: str
    synopsis: str | None
    style_config: dict[str, Any]
    schedule_config: dict[str, Any]
    status: str
    created_at: datetime
    updated_at: datetime
    chapter_count: int = 0
    published_count: int = 0
    model_config = {"from_attributes": True}
```

- [ ] **Step 3: 创建 chapter.py, generation.py**

chapter.py 包含 `ChapterUpdate`, `ChapterResponse`；generation.py 包含 `GenerateOutlineRequest`, `GenerateChapterRequest`, `GenerationTaskResponse`。

- [ ] **Step 4: 提交**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas"
```

### Task 3.2: Auth 中间件与数据库会话

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/router.py`

- [ ] **Step 1: 创建 deps.py** — async engine + async session + Bearer token 验证（无 token 时 dev 模式跳过）
- [ ] **Step 2: 创建 v1 router** — `APIRouter(prefix="/api/v1")`
- [ ] **Step 3: 注册到 main.py** — `app.include_router(v1_router)`
- [ ] **Step 4: 提交**

```bash
git add backend/app/api/
git commit -m "feat: add auth middleware and DB session dependency"
```

### Task 3.3: 基础 CRUD Services

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/novel_service.py`
- Create: `backend/app/services/chapter_service.py`

实现 `NovelService`（list/get/create/update/update_style/delete）和 `ChapterService`（list/get/update/publish/get_latest_number），使用 async SQLAlchemy。

- [ ] **Step 1: 实现并提交**

```bash
git add backend/app/services/
git commit -m "feat: add NovelService and ChapterService"
```

---

## Chunk 4: REST API Routes

### Task 4.1: Novel & Chapter 路由

**Files:**
- Create: `backend/app/api/v1/novels.py`
- Create: `backend/app/api/v1/chapters.py`

实现 novels CRUD（GET POST /novels, GET PATCH DELETE /novels/{id}, PATCH /novels/{id}/style）和 chapters（GET /novels/{id}/chapters, GET PATCH /chapters/{id}, POST /chapters/{id}/publish）。

- [ ] **Step 1: 实现并注册路由，提交**

### Task 4.2: 角色、世界观、大纲、生成、RAG API

**Files:**
- Create: `backend/app/api/v1/characters.py`
- Create: `backend/app/api/v1/world_settings.py`
- Create: `backend/app/api/v1/outlines.py`
- Create: `backend/app/api/v1/generation.py`
- Create: `backend/app/api/v1/rag.py`

generation.py 包含 SSE 端点 `GET /generation/stream/{task_id}` 通过 sse-starlette 实现流式推送。

- [ ] **Step 1: 实现并注册所有路由，提交**

---

## Chunk 5: RAG 引擎

### Task 5.1: RAG Pipeline

**Files:**
- Create: `backend/app/ai/__init__.py`
- Create: `backend/app/ai/rag/__init__.py`
- Create: `backend/app/ai/rag/splitter.py`
- Create: `backend/app/ai/rag/embedder.py`
- Create: `backend/app/ai/rag/retriever.py`
- Create: `backend/app/services/rag_service.py`

- [ ] **Step 1: 创建 splitter.py** — LangChain `RecursiveCharacterTextSplitter(chunk_size=800, overlap=100)`，中文分隔符
- [ ] **Step 2: 创建 embedder.py** — OpenAI `text-embedding-3-small`，单例模式
- [ ] **Step 3: 创建 retriever.py** — `hybrid_search()`：向量检索 top10 + ILIKE 关键词 top5 → RRF 融合 → top5
- [ ] **Step 4: 创建 RagService** — upload/list/delete/search
- [ ] **Step 5: 提交**

```bash
git add backend/app/ai/rag/ backend/app/services/rag_service.py
git commit -m "feat: add RAG engine with hybrid search"
```

---

## Chunk 6: AI Agents & Prompts

### Task 6.1: Prompt Templates

**Files:**
- Create: `backend/app/ai/prompts/__init__.py`
- Create: `backend/app/ai/prompts/outline.py`
- Create: `backend/app/ai/prompts/writing.py`
- Create: `backend/app/ai/prompts/review.py`

三个模板文件包含完整的 System/User prompt 字符串，变量通过 `.format()` 注入。

- [ ] **Step 1: 实现并提交**

### Task 6.2: LangChain Agents

**Files:**
- Create: `backend/app/ai/agents/__init__.py`
- Create: `backend/app/ai/agents/outline_agent.py`
- Create: `backend/app/ai/agents/writing_agent.py`
- Create: `backend/app/ai/agents/review_agent.py`

- [ ] **Step 1: 实现 OutlineAgent** — `ChatOpenAI(temperature=0.8, max_tokens=4000)` → System/User message → 解析响应为 outline dict list
- [ ] **Step 2: 实现 WritingAgent** — 分段生成（opening/development/climax/ending），每段通过 `on_segment` 回调推送，temperature=0.9
- [ ] **Step 3: 实现 ReviewAgent** — 五维检查，JSON 格式输出，temperature=0.3
- [ ] **Step 4: 提交**

```bash
git add backend/app/ai/prompts/ backend/app/ai/agents/
git commit -m "feat: add three AI agents with prompt templates"
```

---

## Chunk 7: MCP Server

### Task 7.1: MCP Server 实现

**Files:**
- Create: `backend/app/mcp/__init__.py`
- Create: `backend/app/mcp/server.py`
- Create: `backend/app/mcp/tools/__init__.py`
- Create: `backend/app/mcp/tools/generation.py`
- Create: `backend/app/mcp/tools/query.py`
- Create: `backend/app/mcp/tools/knowledge.py`
- Create: `backend/app/mcp/tools/consistency.py`
- Create: `backend/app/mcp/resources/__init__.py`
- Create: `backend/app/mcp/resources/novel_resources.py`
- Create: `backend/app/mcp/prompts/__init__.py`
- Create: `backend/app/mcp/prompts/writing_prompts.py`

- [ ] **Step 1: 创建 server.py** — `Server("novel-writing-agent")` + SSE transport
- [ ] **Step 2: 注册 8 个 Tools**（generation/query/knowledge/consistency 四个分组文件）
- [ ] **Step 3: 注册 3 个 Resources**（novel://{id}/outline, characters, style）
- [ ] **Step 4: 注册 2 个 Prompts**（continue_writing, character_dialogue）
- [ ] **Step 5: 挂载到 FastAPI** — `/mcp` 路径
- [ ] **Step 6: 提交**

```bash
git add backend/app/mcp/
git commit -m "feat: add MCP server with 8 tools, 3 resources, 2 prompts"
```

---

## Chunk 8: Celery 任务与 SSE

### Task 8.1: 异步生成任务

**Files:**
- Create: `backend/app/tasks/__init__.py`
- Create: `backend/app/tasks/celery_app.py`
- Create: `backend/app/tasks/generation_tasks.py`

- [ ] **Step 1: 创建 Celery app** — Redis broker/backend，配置 task 重试策略
- [ ] **Step 2: 创建 generate_chapter_task** — 同步 DB 会话 + asyncio.run_until_complete 包装异步 Agent 调用
- [ ] **Step 3: 实现 SSE 推送** — Redis pub/sub 发布 progress/content/complete 事件
- [ ] **Step 4: 添加 Celery Beat 定时任务** — 扫描启用计划的小说，自动创建 generation task
- [ ] **Step 5: 提交**

```bash
git add backend/app/tasks/
git commit -m "feat: add Celery async tasks and SSE streaming"
```

---

## Chunk 9: 前端核心

### Task 9.1: UI 基础设施

**Files:**
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/components/ui/card.tsx`
- Create: `frontend/src/components/ui/badge.tsx`
- Create: `frontend/src/components/ui/tabs.tsx`
- Create: `frontend/src/components/ui/dialog.tsx`
- Create: `frontend/src/components/layout/sidebar.tsx`

- [ ] **Step 1: 创建 cn() utils + API client + 基础 UI 组件 + 布局组件**
- [ ] **Step 2: 提交**

### Task 9.2: 页面实现

**Files:**
- Create: `frontend/src/app/projects/page.tsx`
- Create: `frontend/src/app/projects/[id]/layout.tsx`
- Create: `frontend/src/app/projects/[id]/page.tsx`
- Create: `frontend/src/app/projects/[id]/settings/page.tsx`
- Create: `frontend/src/app/projects/[id]/chapters/page.tsx`
- Create: `frontend/src/app/projects/[id]/review/page.tsx`
- Create: `frontend/src/app/projects/[id]/generation/page.tsx`

- [ ] **Step 1: 仪表盘** — 进度卡片 + 快捷操作 + Token 用量
- [ ] **Step 2: 小说列表** — 卡片网格 + 创建弹窗
- [ ] **Step 3: 工作台** — 三栏布局：大纲树 + 章节阅读 + 快捷面板
- [ ] **Step 4: 设定工坊** — Tab 页：基础/风格/角色/世界观/知识库
- [ ] **Step 5: 章节管理** — 状态标签表格 + 筛选
- [ ] **Step 6: 审核编辑台** — 双栏对比 + 审校报告浮层 + 批准/重写
- [ ] **Step 7: 生成控制台** — SSE 流式预览 + 任务历史 + 定时配置
- [ ] **Step 8: 提交**

```bash
git add frontend/src/app/
git commit -m "feat: implement all frontend pages"
```

---

## Chunk 10: 集成测试与 Docker 验证

- [ ] **Step 1: 后端测试** — `pytest` + `httpx.AsyncClient`，覆盖 novels/chapters/generation API
- [ ] **Step 2: Docker Compose 启动验证** — `docker compose up -d` + health check
- [ ] **Step 3: 端到端测试** — 创建小说 → 角色 → 大纲 → 章节 → 审核 → 发布

```bash
git add backend/tests/
git commit -m "test: add API tests and Docker verification"
```

---

## Chunk 11: README 文档

- [ ] **Step 1: 编写 README.md** — 项目介绍、技术栈、快速启动、项目结构
- [ ] **Step 2: 最终提交**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## 执行顺序与依赖

| 顺序 | Chunk | 预估 | 依赖 |
|------|-------|------|------|
| 1 | 项目脚手架 | 30 min | - |
| 2 | 数据库层 | 45 min | 1 |
| 3 | 后端核心层 | 60 min | 2 |
| 4 | REST API Routes | 60 min | 3 |
| 5 | RAG 引擎 | 45 min | 4 |
| 6 | AI Agents | 60 min | 5 |
| 7 | MCP Server | 60 min | 6 |
| 8 | Celery 任务 | 45 min | 7 |
| 9 | 前端核心 | 90 min | 4 |
| 10 | 集成测试 | 30 min | 1-9 |
| 11 | README | 15 min | All |
| **总计** | | **~9 hours** | |

> 前端 Chunk 9 和后端 Chunks 5-8 可并行开发（接口契约在前 4 个 Chunk 已确定）。

---

## 实现注意事项（审查修正）

以下问题在审查中指出，实现时务必注意：

1. **DATABASE_URL** — FastAPI async 需要 `postgresql+asyncpg://`，Celery sync 需要 `postgresql://`。方案：config 中存储 `postgresql://` 格式，FastAPI 端 deps.py 中 `replace("postgresql://", "postgresql+asyncpg://")` 转换，Celery 端直接用原值

2. **pyproject.toml** — 删除了不存在的 `alembic-postgresql` 依赖；添加了 `[tool.setuptools.packages.find]` 配置保证 `pip install .` 正确发现包

3. **docker-compose.yml** — 删除了已废弃的 `version: "3.9"` 声明

4. **/health 端点** — 需检查 DB (SELECT 1)、Redis (PING)、OpenAI (简单 API 调用) 的连通性，而非仅返回静态 JSON

5. **IVFFlat 索引** — 在 Alembic 迁移中需手动添加：`CREATE INDEX ON chapters USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)`；同理 characters/world_settings/rag_chunks

6. **Token 追踪** — generation_meta JSONB 中需记录 `tokens_used`，由 Agent 从 `response.response_metadata.token_usage` 提取

7. **缺失的 API 端点** — 实现时需补充：`PATCH /outlines/{id}/reorder`、`POST /chapters/{id}/rewrite`、`POST /generation/tasks/{task_id}/cancel`

8. **Chunk 9.2 拆分** — 建议将 7 个页面拆分为 2-3 个子任务：仪表盘+小说列表 → 工作台+设定工坊 → 章节管理+审核+生成

9. **logging.py 循环导入** — 避免 `__import__("app.config").config.settings` 方式，改为在 `setup_logging()` 调用时由外部传入 debug 标志

10. **Outline 模型** — 统一使用 `back_populates` 代替 `backref`，保持风格一致

