# 小说智能写作助手

AI 驱动的中文武侠/网文自动写作系统，覆盖从世界观构建、角色设计到连载章节生成与质量审校的完整创作生命周期。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 14、React 18、Tailwind CSS、Radix UI |
| 后端 | FastAPI、SQLAlchemy 2.0 (异步)、Celery |
| AI | LangChain、OpenAI 兼容接口（支持 GPT-4o / DeepSeek 等）、text-embedding-3-small |
| 数据库 | PostgreSQL 16 + pgvector（IVFFlat + 余弦相似度） |
| 缓存 / 队列 | Redis（Celery 消息代理、SSE 发布订阅） |
| MCP | 自建 MCP Server（16 个工具、7 个资源、6 个提示词） |
| 部署 | Docker Compose（6 个服务） |

## 快速开始

### 环境要求

- Docker 和 Docker Compose
- OpenAI 兼容 API Key（支持 DeepSeek、OpenAI 等）

### 安装步骤

```bash
# 1. 克隆项目
cd agent

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env → 设置 OPENAI_API_KEY=sk-your-key
# 如使用 DeepSeek，设置 OPENAI_BASE_URL=https://api.deepseek.com/v1

# 3. 启动所有服务
docker compose up -d

# 4. 执行数据库迁移
docker compose exec backend alembic upgrade head

# 5. 打开应用
# 前端: http://localhost:3000
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| `frontend` | 3000 | Next.js Web 界面 |
| `backend` | 8000 | FastAPI REST API + SSE 流式推送 |
| `worker` | — | Celery 异步任务执行（章节/大纲生成） |
| `beat` | — | Celery Beat 定时调度（自动生成触发器） |
| `db` | 5432 | PostgreSQL 16 + pgvector |
| `redis` | 6379 | Redis（消息代理、发布订阅、调度持久化） |

## 功能特性

### 小说全生命周期管理
- 创建小说，设定类型、梗概和自定义风格配置
- 配置行文基调、叙事视角、每章目标字数和自定义写作指令
- 按章节数量和发布状态追踪写作进度

### 世界观与角色工坊
- 设计世界观设定，支持分类管理（地域、势力、功法体系等）
- 创建角色档案，包含角色定位、描述和结构化属性
- 所有设定自动向量化嵌入，供 AI 上下文检索

### 大纲规划
- 树形层级大纲：卷 → 弧线 → 章节
- 支持拖拽排序，灵活调整父子关系
- 任意层级 AI 大纲生成

### AI 章节生成
- 四阶段分段生成：开篇 → 发展 → 高潮 → 收尾
- 实时 SSE 流式预览生成内容
- 手动触发，可自定义每章目标字数
- 上下文感知：自动注入大纲、角色档案和 RAG 知识库内容
- 偏差自动修正：章节字数与目标偏差超过 15% 时自动调整
- 生成后自动提取角色信息、合并角色档案
- 可选的内容审核（敏感词过滤）

### 审校与发布流程
- AI 五维质量审校：剧情连贯性、角色一致性、节奏把控、文笔质量、对话水准
- 分屏审校台：原文与编辑区同屏对照，支持通过/重写操作
- 草稿 → 审校中 → 已发布 状态流转

### RAG 知识库
- 上传参考文档（世界观资料、写作指南、风格参考等）
- 中文感知的智能文本分割（`。！？，` 等中文标点识别）
- 混合检索：向量相似度（余弦） + 关键词（ILIKE） → RRF 融合排序
- 检索到的上下文自动注入生成提示词

### 定时自动生成
- 支持按小说配置 cron 定时计划
- Celery Beat 每 5 分钟扫描到期章节
- 任务历史记录与状态追踪

### AI 角色自动提取
- 章节生成后自动识别新出场角色
- 跨章节合并角色档案，追踪出场记录
- 保持角色信息的一致性和完整性

### 世界观一致性检测
- 新设定创建时 AI 自动检测与已有设定的矛盾
- 结合 RAG 知识库进行交叉验证
- 审校环节支持设定合规性专项检查

## 项目结构

```
agent/
├── docker-compose.yml
├── .env.example
├── README.md
├── docs/
│   └── superpowers/
│       ├── specs/          # 设计文档
│       └── plans/          # 实现计划
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 测试套件
│   └── app/
│       ├── main.py         # FastAPI 应用入口
│       ├── config.py       # Pydantic 配置（环境变量）
│       ├── api/
│       │   ├── deps.py     # 认证 + 数据库会话依赖注入
│       │   └── v1/         # REST API 路由（7 个模块）
│       ├── models/         # SQLAlchemy 模型（8 个实体）
│       ├── schemas/        # Pydantic 请求/响应模型
│       ├── services/       # 业务逻辑层（8 个服务）
│       ├── ai/
│       │   ├── agents/     # 5 个 AI 智能体（大纲/写作/审校/角色/世界观）
│       │   ├── prompts/    # 提示词模板（5 个场景 + 版本管理）
│       │   └── rag/        # 文本分割器、嵌入器、检索引擎
│       ├── mcp/
│       │   ├── server.py   # MCP Server 定义（FastMCP）
│       │   ├── tools/      # 16 个 MCP 工具（生成/查询/知识库/一致性/管理）
│       │   ├── resources/  # 7 个 MCP 资源（大纲/角色/风格/章节/世界观/概览）
│       │   └── prompts/    # 6 个 MCP 提示词模板
│       ├── tasks/
│       │   ├── celery_app.py           # Celery 配置
│       │   └── generation_tasks.py     # 异步生成任务
│       └── utils/
│           └── logging.py  # 结构化日志（structlog）
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.ts
    ├── next.config.js
    └── src/
        ├── app/            # Next.js App Router 页面
        │   ├── page.tsx                    # 仪表盘
        │   ├── projects/                   # 小说列表 + 创建
        │   └── projects/[id]/              # 工作台（设置/章节/审校/生成/大纲）
        ├── components/
        │   ├── ui/         # shadcn 风格组件（Button、Card、Badge、Dialog、Tabs）
        │   └── layout/     # 侧边导航栏
        ├── lib/
        │   ├── api.ts      # 完整 API 客户端
        │   └── utils.ts    # cn() 工具函数
        └── types/
            └── index.ts    # TypeScript 类型定义
```

## API 概览

### 小说管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels` | 获取小说列表 |
| POST | `/api/v1/novels` | 创建小说 |
| GET | `/api/v1/novels/{id}` | 获取小说详情 |
| PATCH | `/api/v1/novels/{id}` | 更新小说信息 |
| DELETE | `/api/v1/novels/{id}` | 删除小说 |
| PATCH | `/api/v1/novels/{id}/style` | 更新写作风格配置 |

### 章节管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{id}/chapters` | 获取章节列表 |
| GET | `/api/v1/chapters/{id}` | 获取章节详情（含正文） |
| PATCH | `/api/v1/chapters/{id}` | 更新章节内容 |
| POST | `/api/v1/chapters/{id}/publish` | 发布章节 |
| POST | `/api/v1/chapters/{id}/review` | AI 审校（五维检查 + RAG） |
| POST | `/api/v1/chapters/{id}/rewrite` | 触发异步重写 |

### 角色管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{id}/characters` | 获取角色列表 |
| POST | `/api/v1/novels/{id}/characters` | 创建角色（自动向量嵌入） |
| GET | `/api/v1/characters/{id}` | 获取角色详情 |
| PATCH | `/api/v1/characters/{id}` | 更新角色（重新嵌入） |
| DELETE | `/api/v1/characters/{id}` | 删除角色 |

### 世界观设定
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{id}/world-settings` | 获取世界观设定列表 |
| POST | `/api/v1/novels/{id}/world-settings` | 创建设定（自动向量嵌入） |
| POST | `/api/v1/novels/{id}/world-settings/check` | AI 一致性检测 |
| GET | `/api/v1/world-settings/{id}` | 获取设定详情 |
| PATCH | `/api/v1/world-settings/{id}` | 更新设定（重新嵌入） |
| DELETE | `/api/v1/world-settings/{id}` | 删除设定 |

### 大纲管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/novels/{id}/outlines` | 获取大纲树（层级结构） |
| POST | `/api/v1/novels/{id}/outlines` | 创建大纲节点 |
| GET | `/api/v1/outlines/{id}` | 获取大纲节点 |
| PATCH | `/api/v1/outlines/{id}` | 更新大纲节点 |
| DELETE | `/api/v1/outlines/{id}` | 删除大纲节点（级联删除子节点） |
| PATCH | `/api/v1/outlines/{id}/reorder` | 调整排序 |

### AI 生成
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/novels/{id}/generate/outline` | 触发 AI 大纲生成 |
| POST | `/api/v1/novels/{id}/generate/chapter` | 触发 AI 章节生成 |
| GET | `/api/v1/generation/tasks` | 获取生成任务列表 |
| GET | `/api/v1/generation/tasks/{id}` | 查询任务状态 |
| POST | `/api/v1/generation/tasks/{id}/cancel` | 取消任务 |
| GET | `/api/v1/generation/stream/{task_id}` | SSE 流式推送 |

### RAG 知识库
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/novels/{id}/rag/documents` | 上传文档（自动分段+嵌入） |
| GET | `/api/v1/novels/{id}/rag/documents` | 获取文档列表 |
| DELETE | `/api/v1/rag/documents/{id}` | 删除文档（级联删除分段） |
| POST | `/api/v1/rag/search` | 混合检索 |

### 系统
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查（数据库 + Redis + AI API） |

## MCP Server

项目内置完整的 MCP（Model Context Protocol）服务，支持 AI 编辑器（如 Claude Code）直接调用小说创作工具。

### 工具（16 个）

#### 生成类
| 工具 | 说明 |
|------|------|
| `generate_outline` | 派发 AI 大纲生成任务 |
| `generate_chapter` | 派发 AI 章节生成任务 |
| `rewrite_section` | 按指令改写指定文本段落 |
| `get_generation_task` | 查询生成任务进度和结果 |

#### 查询类
| 工具 | 说明 |
|------|------|
| `query_characters` | 语义 + 关键词检索角色及知识库 |
| `query_plot_context` | 检索相关已写章节，保持剧情一致 |
| `get_writing_context` | 聚合当前写作所需全部上下文 |

#### 知识库类
| 工具 | 说明 |
|------|------|
| `search_knowledge_base` | RAG 混合检索用户上传的参考资料 |
| `upload_knowledge_document` | 上传文档到知识库，自动分段嵌入 |

#### 一致性检测
| 工具 | 说明 |
|------|------|
| `check_consistency` | 检查章节与角色/世界观设定的矛盾 |

#### 数据管理
| 工具 | 说明 |
|------|------|
| `create_character` / `update_character` | 角色 CRUD |
| `create_world_setting` / `update_world_setting` | 世界观设定 CRUD |
| `create_outline` / `update_outline` | 大纲 CRUD |

### 资源（7 个）

| 资源 URI | 说明 |
|----------|------|
| `novel://{id}/outline` | 完整大纲树 JSON |
| `novel://{id}/characters` | 全部角色档案 |
| `novel://{id}/style` | 写作风格配置 |
| `novel://{id}/chapters` | 所有章节目录元数据 |
| `novel://{id}/chapter/{number}` | 指定章节完整正文 |
| `novel://{id}/world-settings` | 世界观设定列表 |
| `novel://{id}/summary` | 小说概览与进度统计 |

### 提示词模板（6 个）

| 提示词 | 说明 |
|--------|------|
| `continue_writing` | 续写提示词（聚合上下文） |
| `character_dialogue` | 角色对话生成提示词 |
| `review_chapter` | 章节五维审校提示词 |
| `brainstorm_plot` | 情节头脑风暴提示词 |
| `create_character` | 角色创建设计提示词 |
| `plan_arc` | 故事弧线/分卷规划提示词 |

## AI 智能体

| 智能体 | 温度 | 用途 |
|--------|------|------|
| **OutlineAgent** | 0.8 | 基于类型、世界观、角色和 RAG 上下文生成大纲节点（卷/弧线/章节） |
| **WritingAgent** | 0.9/阶段 | 四阶段分段生成章节（开篇 20% → 发展 35% → 高潮 25% → 收尾 20%），含字数偏差修正 |
| **ReviewAgent** | 0.3 | 五维质量审校（角色一致性、剧情连贯性、设定合规性、风格一致性、篇幅控制），输出 JSON 结果 |
| **CharacterAgent** | 0.3 | 从章节中自动识别提取角色，跨章节合并档案，追踪出场记录 |
| **WorldSettingAgent** | 0.2 | 检测新世界设定与已有设定的矛盾，结合 RAG 交叉验证 |

所有智能体内置指数退避重试（最多 3 次）、API Key 轮换和 LLM 响应缓存。上下文按比例截断（总计上限 12000 字符）。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_KEY` | — | API Key（支持逗号分隔多个实现轮换） |
| `OPENAI_BASE_URL` | 空 | 自定义 API 端点（如 `https://api.deepseek.com/v1`） |
| `OPENAI_MODEL` | `gpt-4o` | 主力生成模型 |
| `OPENAI_FALLBACK_MODEL` | `gpt-4o-mini` | 重试耗尽后的降级模型 |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | 文本嵌入模型（1536 维） |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL 连接字符串 |
| `REDIS_URL` | `redis://redis:6379/0` | Redis 连接字符串 |
| `ACCESS_TOKEN` | `change-me` | Bearer 认证令牌（值为 `change-me` 时跳过认证） |
| `LLM_CACHE_ENABLED` | `True` | LLM 响应内存缓存开关 |
| `CONTENT_MODERATION_ENABLED` | `True` | 内容审核开关 |
| `CONTENT_MODERATION_BLOCKED_WORDS` | 空 | 敏感词列表（逗号分隔） |
| `DEBUG` | `False` | 调试模式（启用 structlog 控制台输出） |

## 测试

```bash
cd backend
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
