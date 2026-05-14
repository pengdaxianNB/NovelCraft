from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.ai.rag.retriever import hybrid_search, hybrid_search_sync
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.rag import RagChunk, RagDocument
from app.models.world_setting import WorldSetting


@dataclass
class RagContextHit:
    source: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    similarity: float | None = None


@dataclass
class RagContextBundle:
    query: str
    hits: list[RagContextHit] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def sources(self) -> list[str]:
        return sorted({hit.source for hit in self.hits})

    def metadata(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "hit_count": len(self.hits),
            "sources": self.sources,
            "warnings": self.warnings,
        }


def _elapsed_ms(start: float) -> float:
    return round((perf_counter() - start) * 1000, 2)


def _clip(text: str | None, limit: int = 900) -> str:
    text = (text or "").strip()
    return text[:limit]


def format_rag_context(bundle: RagContextBundle) -> str:
    if not bundle.hits:
        return ""

    groups: dict[str, list[RagContextHit]] = {}
    for hit in bundle.hits:
        groups.setdefault(hit.source, []).append(hit)

    parts: list[str] = []
    for source, hits in groups.items():
        parts.append(f"## {source}")
        for hit in hits:
            title = hit.title or source
            parts.append(f"[{title}]\n{_clip(hit.content)}")
    return "\n\n".join(parts)


def _make_query(*parts: str | None, limit: int = 500) -> str:
    query = " ".join((p or "").strip() for p in parts if (p or "").strip())
    return query[:limit] or "novel context"


def _profile_text(profile: dict[str, Any] | None) -> str:
    if not profile:
        return ""
    return "; ".join(f"{k}: {v}" for k, v in profile.items())


class AsyncRagContextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_chapter_context(
        self,
        novel_id: str,
        outline_summary: str,
        description: str | None,
        chapter_number: int,
    ) -> RagContextBundle:
        query = _make_query(outline_summary, description, f"chapter {chapter_number}")
        return await self._build_context(novel_id, query, chapter_number=chapter_number)

    async def build_outline_context(
        self,
        novel_id: str,
        level: str,
        parent_title: str,
        instruction: str | None = "",
    ) -> RagContextBundle:
        query = _make_query(level, parent_title, instruction)
        return await self._build_context(novel_id, query)

    async def build_review_context(
        self,
        novel_id: str,
        chapter_content: str,
        chapter_number: int,
        include_project_materials: bool = True,
    ) -> RagContextBundle:
        query = _make_query(chapter_content[:700], f"chapter {chapter_number}")
        return await self._build_context(
            novel_id,
            query,
            chapter_number=chapter_number,
            include_project_materials=include_project_materials,
        )

    async def build_world_setting_context(
        self,
        novel_id: str,
        category: str,
        title: str,
        content: str,
    ) -> RagContextBundle:
        query = _make_query(category, title, content[:700])
        return await self._build_context(novel_id, query)

    async def _build_context(
        self,
        novel_id: str,
        query: str,
        chapter_number: int | None = None,
        include_project_materials: bool = True,
    ) -> RagContextBundle:
        bundle = RagContextBundle(query=query)

        start = perf_counter()
        try:
            results = await hybrid_search(self.db, novel_id, query, top_k=5)
            for item in results:
                metadata = item.get("metadata") or {}
                bundle.hits.append(RagContextHit(
                    source="knowledge",
                    title=str(metadata.get("filename") or "knowledge"),
                    content=str(item.get("content") or ""),
                    metadata=metadata,
                    similarity=item.get("similarity"),
                ))
        except Exception as exc:
            await self.db.rollback()
            bundle.warnings.append(f"knowledge search failed: {exc}")
        bundle.timings_ms["knowledge_search"] = _elapsed_ms(start)

        if not include_project_materials:
            return bundle

        start = perf_counter()
        try:
            bundle.hits.extend(await self._world_hits(novel_id))
        except Exception as exc:
            await self.db.rollback()
            bundle.warnings.append(f"world search failed: {exc}")
        bundle.timings_ms["world_search"] = _elapsed_ms(start)

        start = perf_counter()
        try:
            bundle.hits.extend(await self._character_hits(novel_id))
        except Exception as exc:
            await self.db.rollback()
            bundle.warnings.append(f"character search failed: {exc}")
        bundle.timings_ms["character_search"] = _elapsed_ms(start)

        start = perf_counter()
        try:
            bundle.hits.extend(await self._chapter_hits(novel_id, chapter_number))
        except Exception as exc:
            await self.db.rollback()
            bundle.warnings.append(f"chapter search failed: {exc}")
        bundle.timings_ms["chapter_search"] = _elapsed_ms(start)
        return bundle

    async def _world_hits(self, novel_id: str) -> list[RagContextHit]:
        result = await self.db.execute(
            select(WorldSetting).where(WorldSetting.novel_id == novel_id).limit(8)
        )
        return [
            RagContextHit("world", f"{ws.category}: {ws.title}", ws.content)
            for ws in result.scalars().all()
        ]

    async def _character_hits(self, novel_id: str) -> list[RagContextHit]:
        result = await self.db.execute(
            select(Character).where(Character.novel_id == novel_id).limit(12)
        )
        return [
            RagContextHit("character", f"{c.name} ({c.role})", _profile_text(c.profile))
            for c in result.scalars().all()
        ]

    async def _chapter_hits(self, novel_id: str, chapter_number: int | None) -> list[RagContextHit]:
        stmt = select(Chapter).where(Chapter.novel_id == novel_id)
        if chapter_number is not None:
            stmt = stmt.where(Chapter.chapter_number < chapter_number)
        stmt = stmt.order_by(Chapter.chapter_number.desc()).limit(5)
        result = await self.db.execute(stmt)
        return [
            RagContextHit(
                "chapter",
                f"Chapter {ch.chapter_number}: {ch.title}",
                _clip(ch.content, 900),
            )
            for ch in result.scalars().all()
            if ch.content
        ]


class SyncRagContextService:
    def __init__(self, db: Session):
        self.db = db

    def build_chapter_context(
        self,
        novel_id: str,
        outline_summary: str,
        description: str | None,
        chapter_number: int,
    ) -> RagContextBundle:
        query = _make_query(outline_summary, description, f"chapter {chapter_number}")
        return self._build_context(novel_id, query, chapter_number=chapter_number)

    def build_outline_context(
        self,
        novel_id: str,
        level: str,
        parent_title: str,
        instruction: str | None = "",
    ) -> RagContextBundle:
        query = _make_query(level, parent_title, instruction)
        return self._build_context(novel_id, query)

    def _build_context(
        self,
        novel_id: str,
        query: str,
        chapter_number: int | None = None,
    ) -> RagContextBundle:
        bundle = RagContextBundle(query=query)

        start = perf_counter()
        try:
            results = hybrid_search_sync(self.db, novel_id, query, top_k=5)
            for item in results:
                metadata = item.get("metadata") or {}
                bundle.hits.append(RagContextHit(
                    source="knowledge",
                    title=str(metadata.get("filename") or "knowledge"),
                    content=str(item.get("content") or ""),
                    metadata=metadata,
                    similarity=item.get("similarity"),
                ))
        except Exception as exc:
            self.db.rollback()
            bundle.warnings.append(f"knowledge search failed: {exc}")
        bundle.timings_ms["knowledge_search"] = _elapsed_ms(start)

        start = perf_counter()
        try:
            for ws in self.db.execute(
                select(WorldSetting).where(WorldSetting.novel_id == novel_id).limit(8)
            ).scalars().all():
                bundle.hits.append(RagContextHit("world", f"{ws.category}: {ws.title}", ws.content))
        except Exception as exc:
            bundle.warnings.append(f"world search failed: {exc}")
        bundle.timings_ms["world_search"] = _elapsed_ms(start)

        start = perf_counter()
        try:
            for c in self.db.execute(
                select(Character).where(Character.novel_id == novel_id).limit(12)
            ).scalars().all():
                bundle.hits.append(
                    RagContextHit("character", f"{c.name} ({c.role})", _profile_text(c.profile))
                )
        except Exception as exc:
            bundle.warnings.append(f"character search failed: {exc}")
        bundle.timings_ms["character_search"] = _elapsed_ms(start)

        start = perf_counter()
        try:
            stmt = select(Chapter).where(Chapter.novel_id == novel_id)
            if chapter_number is not None:
                stmt = stmt.where(Chapter.chapter_number < chapter_number)
            stmt = stmt.order_by(Chapter.chapter_number.desc()).limit(5)
            for ch in self.db.execute(stmt).scalars().all():
                if ch.content:
                    bundle.hits.append(
                        RagContextHit("chapter", f"Chapter {ch.chapter_number}: {ch.title}", _clip(ch.content))
                    )
        except Exception as exc:
            bundle.warnings.append(f"chapter search failed: {exc}")
        bundle.timings_ms["chapter_search"] = _elapsed_ms(start)
        return bundle
