# 自动写小说 Agent 系统设计

## 概述

一个基于 AI 的网文自动写作系统，支持世界观/角色设定、大纲规划、章节自动生成、人工审核编辑、知识库 RAG 增强。单人使用，Web 界面操作。

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 14 (App Router) + shadcn/ui + Tailwind CSS |
| 后端 | Python FastAPI + Celery |
| AI | LangChain + OpenAI (GPT-4o) + langchain-mcp-adapters |
| 数据库 | PostgreSQL 16 + pgvector，迁移用 Alembic |
| 缓存/队列 | Redis 7 |
| 协议 | REST API + MCP (Model Context Protocol) + SSE |
| 部署 | Docker Compose |

## 系统架构

```
Next.js 前端 (port 3000)
    │ REST + SSE（通过 CORS 或 nginx 代理）
FastAPI 后端 (port 8000)
    ├── REST API (/api/v1/*) — 前端 CRUD 操作
    ├── MCP Server (/mcp) — 仅服务 AI Agent，不走前端
    ├── Celery Worker — 异步执行生成任务
    └── Celery Beat — 定时触发（Redis 持久化 schedule）
        │
PostgreSQL + pgvector │ Redis
```

### 关键架构决策

- **认证**：单人使用，不实现用户系统。后端通过环境变量 `ACCESS_TOKEN` 做简单 Bearer Token 校验
- **CORS**：开发环境 FastAPI 配置 `allow_origins=["http://localhost:3000"]`；生产用 nginx 反向代理消除跨域
- **MCP vs REST**：MCP Resources 服务于 AI Agent 的上下文获取（返回 LLM 友好的结构化数据），REST API 服务于前端 UI 的 CRUD 操作。职责不同，不重复
- **Celery Beat 持久化**：使用 `celery-beat-redis` scheduler，schedules 存 Redis，重启不丢失

## 项目结构

```
agent/
├── docker-compose.yml
├── .env.example
├── frontend/                    # Next.js
│   └── src/
│       ├── app/                 # 页面路由
│       │   ├── page.tsx         # 仪表盘
│       │   ├── projects/        # 小说管理
│       │   └── projects/[id]/   # 设定工坊/章节/审核/生成控制台
│       ├── components/          # UI 组件
│       ├── hooks/               # 自定义 hooks
│       ├── lib/                 # 工具函数、API client
│       └── types/               # TypeScript 类型
├── backend/
│   ├── alembic/                 # 数据库迁移
│   ├── app/
│   │   ├── api/v1/              # REST 路由
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic 模型
│   │   ├── services/            # 业务逻辑
│   │   ├── ai/                  # AI 层
│   │   │   ├── agents/          # 三个 Agent
│   │   │   ├── chains/          # LangChain Chains
│   │   │   ├── prompts/         # Prompt 模板
│   │   │   └── rag/             # RAG 引擎
│   │   ├── mcp/                 # MCP Server
│   │   │   ├── server.py
│   │   │   ├── tools/
│   │   │   ├── resources/
│   │   │   └── prompts/
│   │   ├── tasks/               # Celery 任务
│   │   └── utils/
│   └── tests/
└── docs/
```

## 数据模型

### 核心表

```sql
novels (id, title, genre, synopsis, style_config JSONB, schedule_config JSONB, status, created_at, updated_at)
characters (id, novel_id FK, name, role, profile JSONB, embedding vector(1536))
world_settings (id, novel_id FK, category, title, content, embedding vector(1536))
outlines (id, novel_id FK, level, parent_id FK, sequence, title, summary, status)
chapters (id, novel_id FK, outline_id FK, chapter_number, title, content, word_count,
          status, embedding vector(1536), generation_meta JSONB)
rag_documents (id, novel_id FK, filename, content, chunk_count, status)
rag_chunks (id, document_id FK, chunk_index, content, embedding vector(1536), metadata JSONB)
generation_tasks (id, novel_id FK, task_type, target_id, status, progress JSONB,
                  result JSONB, error_message, started_at, completed_at)
```

### 向量空间说明

- **故事一致性向量**：chapters.embedding, characters.embedding, world_settings.embedding — 三个表各自独立存储，检索时按需查询对应表
- **RAG 知识库向量**：rag_chunks.embedding — 独立表，与故事数据隔离
- 均使用 OpenAI text-embedding-3-small（1536维），IVFFlat 索引 + cosine similarity

### 写作风格配置 (style_config JSONB)

```json
{
  "tone": "轻松|严肃|幽默|热血",
  "pov": "第一人称|第三人称|混合",
  "words_per_chapter": 3000,
  "custom_instructions": "自定义写作指令文本"
}
```

单章生成时可覆盖 words_per_chapter，过渡章节写短、高潮章节写长。

## MCP Server

### Tools（8个）与 Agent 的映射

| 工具 | 调用者 | 功能 |
|------|--------|------|
| `generate_outline` | OutlineAgent | 生成新大纲节点 |
| `generate_chapter` | WritingAgent | 生成章节正文（流式） |
| `rewrite_section` | ReviewAgent | 按指令重写段落 |
| `query_characters` | OutlineAgent / WritingAgent / ReviewAgent | 语义检索相关角色 |
| `query_plot_context` | WritingAgent / ReviewAgent | 检索已有章节片段 |
| `search_knowledge_base` | 三个 Agent 均可 | RAG 检索用户文档 |
| `check_consistency` | ReviewAgent | 检查章节与设定的矛盾 |
| `get_writing_context` | WritingAgent | 聚合当前写作所需全部上下文 |

### Resources（3个）

仅服务 AI Agent，获取大块上下文数据：
- `novel://{id}/outline` — 完整大纲树 JSON
- `novel://{id}/characters` — 全部角色档案列表
- `novel://{id}/style` — 写作风格配置

### Prompts（2个）

- `continue_writing` — 根据当前进度生成续写提示词
- `character_dialogue` — 为特定角色生成对话提示词

传输层：SSE，挂载在 FastAPI `/mcp` 路径。前端不直接调用 MCP。

## AI Pipeline

### Agent 1：大纲规划器 (OutlineAgent)
- 输入：novel_id，目标层级，父节点
- 调用的 MCP 工具：query_characters, query_plot_context, search_knowledge_base
- 输出：若干 outline 记录写入数据库

### Agent 2：章节写作器 (WritingAgent)
- 输入：novel_id，outline_id，chapter_number
- 调用的 MCP 工具：get_writing_context, query_characters, query_plot_context, search_knowledge_base
- 生成策略：分段写作（开场→发展→高潮→收尾），每段流式推送 SSE
- 输出：章节 body 正文，status = draft

### Agent 3：审校器 (ReviewAgent)
- 触发时机：WritingAgent 完成后自动执行
- 输入：chapter_id，chapter_content
- 调用的 MCP 工具：check_consistency, query_characters
- 检查维度：角色一致性、情节连续性、设定合规、文风一致、字数达标
- 输出：
  - 通过 → 章节 status 更新为 `review`，附带审校报告 JSON
  - 有问题 → 自动调用 rewrite_section 修复后仍标 `review`，报告标注"已自动修复"项

### 完整工作流

```
用户触发生成
    │
    ▼
Celery 任务入队 → Worker 执行
    │
    ▼
WritingAgent.generate_chapter()
    ├── 通过 MCP 调用 get_writing_context 聚合上下文
    ├── 分段写作（逐段 SSE 推送前端）
    └── 写入 chapter (status=draft)
    │
    ▼
ReviewAgent.review()
    ├── check_consistency
    ├── 发现问题 → rewrite_section → 重新检查
    └── 写入审校报告，status → review
    │
    ▼
前端审核编辑台展示章节
    ├── 用户编辑 → 保存
    ├── 用户批准 → status → published
    └── 用户拒绝 → 触发重新生成
```

### 定时自动生成

Celery Beat 支持为每本小说配置定时生成计划：
- 计划配置存储在 `novels` 表扩展字段 `schedule_config JSONB`：`{"enabled": true, "cron": "0 */6 * * *"}`
- Beat 每个周期检查所有启用计划的小说，自动创建 generation_task 入队
- 用户可在前端随时启用/暂停/修改计划

## RAG 引擎

```
文档上传 → RecursiveCharacterTextSplitter(chunk_size=800, overlap=100)
         → OpenAI text-embedding-3-small → pgvector (rag_chunks 表)
         → 检索时：向量检索(top10) + BM25关键词检索(top5) → RRF融合 → top5 注入 prompt
```

## 错误处理与可观测性

- **日志**：结构化日志（structlog），每行 JSON 格式，包含 trace_id 跟踪整个生成链路
- **生成任务失败处理**：Celery 自动重试（max 3次，指数退避），最终失败标记 status=failed + error_message
- **OpenAI API 限流**：tenacity 库实现 retry + exponential backoff；可配置多个 API key 轮转
- **Token 用量追踪**：每次生成记录 tokens_used 到 generation_meta，前端仪表盘展示用量趋势
- **健康检查**：`/health` 端点检查 DB、Redis、OpenAI 连通性

## API 设计

Base: `/api/v1`

- `GET/POST /novels` — 列表 / 创建
- `GET/PATCH/DELETE /novels/{id}` — 详情 / 更新 / 软删除
- `PATCH /novels/{id}/style` — 更新写作风格
- `GET/POST /novels/{id}/characters` — 角色列表 / 创建
- `GET/PATCH/DELETE /characters/{id}` — 角色详情 / 更新 / 删除
- `GET/POST /novels/{id}/world-settings` — 世界观列表 / 创建
- `PATCH/DELETE /world-settings/{id}` — 更新 / 删除
- `GET/POST /novels/{id}/outlines` — 大纲树 / 创建节点
- `PATCH/DELETE /outlines/{id}` — 更新 / 删除
- `PATCH /outlines/{id}/reorder` — 拖拽重排
- `GET /novels/{id}/chapters` — 章节列表
- `GET/PATCH /chapters/{id}` — 详情 / 编辑
- `POST /chapters/{id}/publish` — 批准发布
- `POST /chapters/{id}/rewrite` — 触发重写
- `POST /novels/{id}/generate/outline` — 触发大纲生成
- `POST /novels/{id}/generate/chapter` — 触发章节生成
- `GET /generation/tasks` — 任务历史
- `GET /generation/tasks/{task_id}` — 任务状态
- `POST /generation/tasks/{task_id}/cancel` — 取消任务
- `GET /generation/stream/{task_id}` — SSE 流式推送
- `POST /novels/{id}/rag/documents` — 上传文档
- `GET /novels/{id}/rag/documents` — 文档列表
- `DELETE /rag/documents/{id}` — 删除文档

## 前端页面

| 路由 | 功能 |
|------|------|
| / | 仪表盘：进度概览、快捷操作、Token 用量 |
| /projects | 小说卡片列表、创建新小说弹窗 |
| /projects/[id] | 工作台：大纲树+章节预览+快捷面板 |
| /projects/[id]/settings | 设定工坊：基础/风格/角色/世界观/知识库(RAG) |
| /projects/[id]/chapters | 章节列表管理（状态标签+筛选） |
| /projects/[id]/review | 审核编辑台：双栏对比+审校报告浮层+批准/重写操作 |
| /projects/[id]/generation | 生成控制台：SSE 流式预览+任务历史+定时配置 |

## 部署

Docker Compose 六服务：

| 服务 | 端口 | 镜像 |
|------|------|------|
| frontend | 3000 | node:20-alpine (Next.js) |
| backend | 8000 | python:3.12-slim (FastAPI + MCP) |
| worker | - | 同上 image，Celery Worker |
| beat | - | 同上 image，Celery Beat (redis scheduler) |
| db | 5432 | pgvector/pgvector:pg16 |
| redis | 6379 | redis:7-alpine |

关键环境变量（.env）：

```
OPENAI_API_KEY=sk-xxx          # 支持逗号分隔多 key 轮转
OPENAI_MODEL=gpt-4o
ACCESS_TOKEN=your-secret-token
DATABASE_URL=postgresql://user:pass@db:5432/novel_agent
REDIS_URL=redis://redis:6379/0
```

本地一键启动：`cp .env.example .env && docker compose up -d`

Alembic 迁移在 backend 容器启动时自动执行（entrypoint 脚本 `alembic upgrade head && uvicorn app.main:app`）。
