"""init

Revision ID: 0001
Revises:
Create Date: 2026-05-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # novels
    op.create_table(
        "novels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("genre", sa.String(50), nullable=False, server_default="玄幻"),
        sa.Column("synopsis", sa.Text),
        sa.Column("style_config", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("schedule_config", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(20), server_default="planning"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # characters
    op.create_table(
        "characters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("novel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("novels.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(50), server_default="配角"),
        sa.Column("profile", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # world_settings
    op.create_table(
        "world_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("novel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("novels.id"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # outlines
    op.create_table(
        "outlines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("novel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("novels.id"), nullable=False),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outlines.id"), nullable=True),
        sa.Column("sequence", sa.Integer, server_default="0"),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("summary", sa.Text),
        sa.Column("status", sa.String(20), server_default="planned"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # chapters
    op.create_table(
        "chapters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("novel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("novels.id"), nullable=False),
        sa.Column("outline_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("outlines.id"), nullable=True),
        sa.Column("chapter_number", sa.Integer, nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text),
        sa.Column("word_count", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="draft"),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("generation_meta", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # rag_documents
    op.create_table(
        "rag_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("novel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("novels.id"), nullable=False),
        sa.Column("filename", sa.String(300), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("chunk_count", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(20), server_default="processing"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # rag_chunks
    op.create_table(
        "rag_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rag_documents.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536)),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # generation_tasks
    op.create_table(
        "generation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("novel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("novels.id"), nullable=False),
        sa.Column("task_type", sa.String(30), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("progress", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for common query patterns
    op.create_index("ix_characters_novel_id", "characters", ["novel_id"])
    op.create_index("ix_world_settings_novel_id", "world_settings", ["novel_id"])
    op.create_index("ix_outlines_novel_id", "outlines", ["novel_id"])
    op.create_index("ix_outlines_parent_id", "outlines", ["parent_id"])
    op.create_index("ix_chapters_novel_id", "chapters", ["novel_id"])
    op.create_index("ix_chapters_outline_id", "chapters", ["outline_id"])
    op.create_index("ix_rag_documents_novel_id", "rag_documents", ["novel_id"])
    op.create_index("ix_rag_chunks_document_id", "rag_chunks", ["document_id"])
    op.create_index("ix_generation_tasks_novel_id", "generation_tasks", ["novel_id"])

    # Vector indexes for similarity search
    op.execute(
        "CREATE INDEX ix_characters_embedding ON characters USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX ix_world_settings_embedding ON world_settings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX ix_chapters_embedding ON chapters USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX ix_rag_chunks_embedding ON rag_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.drop_table("generation_tasks")
    op.drop_table("rag_chunks")
    op.drop_table("rag_documents")
    op.drop_table("chapters")
    op.drop_table("outlines")
    op.drop_table("world_settings")
    op.drop_table("characters")
    op.drop_table("novels")
