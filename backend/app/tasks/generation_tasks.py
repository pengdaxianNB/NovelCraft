import asyncio
import json
from datetime import datetime, timezone

import redis
from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.ai.agents.character_agent import CharacterAgent
from app.ai.agents.outline_agent import OutlineAgent
from app.ai.agents.writing_agent import WritingAgent
from app.config import settings
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.generation_task import GenerationTask
from app.models.novel import Novel
from app.models.outline import Outline
from app.models.world_setting import WorldSetting
from app.ai.prompts.versions import get_prompt_versions
from app.ai.rag.embedder import embed_query
from app.services.content_moderation import get_moderation_service
from app.services.rag_context_service import SyncRagContextService, format_rag_context
from app.utils.logging import get_logger, set_trace_id

logger = get_logger(__name__)
sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(sync_url)


def merge_character_profile(
    existing_profile: dict | None,
    extracted_data: dict,
    chapter_number: int,
) -> dict:
    merged = dict(existing_profile or {})
    extracted_profile = extracted_data.get("profile") or {}
    for key, value in extracted_profile.items():
        if value in (None, "", "unknown", "Unknown", "未知"):
            continue
        existing = merged.get(key)
        if not existing:
            merged[key] = value
        elif isinstance(existing, str) and isinstance(value, str) and len(value) > len(existing):
            merged[key] = value

    evidence = (extracted_data.get("evidence") or "").strip()
    if evidence:
        appearances = list(merged.get("appearances") or [])
        appearances.append({
            "chapter_number": chapter_number,
            "evidence": evidence[:500],
        })
        merged["appearances"] = appearances[-20:]

    merged["last_seen_chapter"] = chapter_number
    return merged


@shared_task(bind=True)
def generate_chapter_task(
    self,
    novel_id: str,
    outline_id: str | None = None,
    chapter_number: int | None = None,
    words_override: int | None = None,
    description: str | None = None,
):
    trace_id = set_trace_id()
    logger.info("Starting chapter generation", trace_id=trace_id, novel_id=novel_id)

    with Session(sync_engine) as db:
        task = db.execute(
            select(GenerationTask).where(GenerationTask.id == self.request.id)
        ).scalar_one_or_none()

        if task:
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            db.commit()

        try:
            novel = db.execute(select(Novel).where(Novel.id == novel_id)).scalar_one()
            style = novel.style_config or {}
            words = words_override or style.get("words_per_chapter", 3000)

            result = asyncio.run(
                _run_generation(db, novel, outline_id, chapter_number or 1, words, description, task_id=str(task.id))
            )

            if task:
                task.status = "done"
                task.result = result
                task.completed_at = datetime.now(timezone.utc)
                db.commit()

        except Exception as e:
            logger.error("Generation failed", error=str(e), trace_id=trace_id)
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
            raise self.retry(exc=e)


async def _run_generation(
    db: Session,
    novel,
    outline_id,
    chapter_number: int,
    words: int,
    description: str | None = None,
    task_id: str = "",
) -> dict:
    agent = WritingAgent()
    segments = []
    r = redis.from_url(settings.redis_url)
    ckpt_key = f"generation:{task_id}:checkpoint"
    checkpoint_ttl = 86400

    resume_from = None
    try:
        raw = r.get(ckpt_key)
        if raw:
            resume_from = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
            logger.info("Found checkpoint, resuming", task_id=task_id, stages=resume_from.get("completed_stages", []))
    except Exception:
        pass

    outline_summary = ""
    if outline_id:
        outline = db.execute(select(Outline).where(Outline.id == outline_id)).scalar_one_or_none()
        if outline:
            outline_summary = f"Title: {outline.title}\nSummary: {outline.summary or ''}"

    previous_context = ""
    prev_chapters = db.execute(
        select(Chapter)
        .where(Chapter.novel_id == novel.id, Chapter.chapter_number < chapter_number)
        .order_by(Chapter.chapter_number.desc())
        .limit(3)
    ).scalars().all()
    if prev_chapters:
        parts = []
        for ch in reversed(prev_chapters):
            excerpt = ch.content[-500:] if ch.content and len(ch.content) > 500 else (ch.content or "")
            parts.append(f"Chapter {ch.chapter_number} {ch.title}\n{excerpt}")
        previous_context = "\n\n".join(parts)

    character_context = ""
    characters = db.execute(
        select(Character).where(Character.novel_id == novel.id)
    ).scalars().all()
    if characters:
        parts = []
        for c in characters:
            profile_parts = [f"{k}: {v}" for k, v in (c.profile or {}).items()]
            parts.append(f"{c.name}({c.role}): {'; '.join(profile_parts)}")
        character_context = "\n".join(parts)

    rag_bundle = SyncRagContextService(db).build_chapter_context(
        novel_id=str(novel.id),
        outline_summary=outline_summary,
        description=description,
        chapter_number=chapter_number,
    )
    rag_context = format_rag_context(rag_bundle)
    rag_meta = rag_bundle.metadata()

    completed_stages: list[str] = []
    accumulated_text = ""

    async def on_segment_with_checkpoint(stage: str, text: str, percent: float):
        nonlocal accumulated_text
        completed_stages.append(stage)
        if text:
            accumulated_text += text + "\n\n"
        segment_data = {"stage": stage, "text": text, "percent": percent}
        segments.append(segment_data)
        try:
            r.publish(f"generation:{task_id}", json.dumps(segment_data, ensure_ascii=False))
        except Exception:
            pass
        try:
            r.setex(ckpt_key, checkpoint_ttl, json.dumps({
                "completed_stages": completed_stages,
                "full_text": accumulated_text,
            }, ensure_ascii=False))
        except Exception:
            pass

    content, word_count, tokens_used = await agent.generate(
        genre=novel.genre,
        tone=novel.style_config.get("tone", "hot-blooded"),
        pov=novel.style_config.get("pov", "third person"),
        words_per_chapter=words,
        style_instructions=novel.style_config.get("custom_instructions", ""),
        outline_summary=outline_summary,
        previous_context=previous_context,
        character_context=character_context,
        rag_context=rag_context,
        description=description or "",
        on_segment=on_segment_with_checkpoint,
        resume_from=resume_from,
    )

    moderation_meta = None
    if settings.content_moderation_enabled:
        mod_result = get_moderation_service().check(content)
        moderation_meta = {
            "passed": mod_result.passed,
            "flags": mod_result.flags,
            "severity": mod_result.severity,
        }

    chapter = Chapter(
        novel_id=novel.id,
        outline_id=outline_id,
        chapter_number=chapter_number,
        title=f"Chapter {chapter_number}",
        content=content,
        word_count=word_count,
        status="draft",
        generation_meta={
            "tokens_used": tokens_used,
            "segments": len(segments),
            "rag_hits": rag_meta["hit_count"],
            "rag_sources": rag_meta["sources"],
            "rag_warnings": rag_bundle.warnings,
            "moderation": moderation_meta,
            "prompt_versions": get_prompt_versions(),
        },
    )
    try:
        chapter.embedding = await embed_query(f"{chapter.title}\n{content[:3000]}")
    except Exception:
        pass

    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    try:
        r.delete(ckpt_key)
    except Exception:
        pass

    created_count = 0
    try:
        char_agent = CharacterAgent()
        existing_names = [c.name for c in characters]
        extracted = await char_agent.extract(
            chapter_content=content,
            existing_characters=existing_names,
            rag_context=rag_context,
        )
        existing_by_name = {c.name.strip().lower(): c for c in characters}
        for char_data in extracted:
            name = (char_data.get("name") or "").strip()
            if not name:
                continue
            existing = existing_by_name.get(name.lower())
            if existing:
                existing.profile = merge_character_profile(existing.profile, char_data, chapter_number)
                if char_data.get("role") and not existing.role:
                    existing.role = char_data["role"]
                continue
            new_char = Character(
                novel_id=novel.id,
                name=name,
                role=char_data.get("role", "supporting"),
                profile=merge_character_profile(char_data.get("profile") or {}, char_data, chapter_number),
            )
            db.add(new_char)
            existing_by_name[name.lower()] = new_char
            created_count += 1
            logger.info("Auto-created character", name=name, role=char_data.get("role", "supporting"))
        db.commit()

        for char_data in extracted:
            name = (char_data.get("name") or "").strip()
            if not name:
                continue
            existing = existing_by_name.get(name.lower())
            if existing:
                try:
                    profile = existing.profile or {}
                    embed_text = f"{existing.name} ({existing.role}): {'; '.join(f'{k}: {v}' for k, v in profile.items())}"
                    existing.embedding = await embed_query(embed_text)
                except Exception:
                    pass
        db.commit()

        logger.info("Character extraction complete", created=created_count, total_extracted=len(extracted))
    except Exception as e:
        logger.warning("Character extraction failed, continuing", error=str(e))

    return {
        "chapter_id": str(chapter.id),
        "word_count": word_count,
        "tokens_used": tokens_used,
        "characters_created": created_count,
        "rag_hits": rag_meta["hit_count"],
        "rag_sources": rag_meta["sources"],
        "rag_warnings": rag_bundle.warnings,
        "timings_ms": {"rag_retrieval": round(sum(rag_bundle.timings_ms.values()), 2)},
    }


@shared_task(bind=True)
def generate_outline_task(self, novel_id: str, level: str, parent_id: str | None, count: int):
    trace_id = set_trace_id()
    logger.info("Starting outline generation", trace_id=trace_id, novel_id=novel_id)

    with Session(sync_engine) as db:
        task = db.execute(
            select(GenerationTask).where(GenerationTask.id == self.request.id)
        ).scalar_one_or_none()

        if task:
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            db.commit()

        try:
            novel = db.execute(select(Novel).where(Novel.id == novel_id)).scalar_one()

            parent_title = ""
            if parent_id:
                parent = db.execute(select(Outline).where(Outline.id == parent_id)).scalar_one_or_none()
                if parent:
                    parent_title = parent.title

            world_context = ""
            world_settings = db.execute(
                select(WorldSetting).where(WorldSetting.novel_id == novel_id)
            ).scalars().all()
            if world_settings:
                world_context = "\n".join(
                    f"[{ws.category}] {ws.title}: {ws.content}" for ws in world_settings
                )

            character_context = ""
            characters = db.execute(
                select(Character).where(Character.novel_id == novel_id)
            ).scalars().all()
            if characters:
                parts = []
                for c in characters:
                    profile_parts = [f"{k}: {v}" for k, v in (c.profile or {}).items()]
                    parts.append(f"{c.name}({c.role}): {'; '.join(profile_parts)}")
                character_context = "\n".join(parts)

            if parent_id:
                existing = db.execute(
                    select(Outline)
                    .where(
                        Outline.novel_id == novel_id,
                        Outline.level == level,
                        Outline.parent_id == parent_id,
                    )
                    .order_by(Outline.sequence)
                ).scalars().all()
            else:
                existing = db.execute(
                    select(Outline)
                    .where(
                        Outline.novel_id == novel_id,
                        Outline.level == level,
                        Outline.parent_id.is_(None),
                    )
                    .order_by(Outline.sequence)
                ).scalars().all()
            existing_outlines = "\n".join(f"- {o.title}: {o.summary or ''}" for o in existing)

            rag_bundle = SyncRagContextService(db).build_outline_context(
                novel_id=novel_id,
                level=level,
                parent_title=parent_title,
                instruction=existing_outlines,
            )
            rag_context = format_rag_context(rag_bundle)
            rag_meta = rag_bundle.metadata()

            agent = OutlineAgent()
            outlines = asyncio.run(
                agent.generate(
                    genre=novel.genre,
                    level=level,
                    parent_title=parent_title,
                    count=count,
                    world_context=world_context,
                    character_context=character_context,
                    existing_outlines=existing_outlines,
                    rag_context=rag_context,
                )
            )
            for i, o in enumerate(outlines):
                outline = Outline(
                    novel_id=novel_id,
                    level=level,
                    parent_id=parent_id,
                    sequence=i,
                    title=o.get("title", f"{level} {i + 1}"),
                    summary=o.get("summary", ""),
                )
                db.add(outline)
            db.commit()

            result = {
                "outlines_created": len(outlines),
                "rag_hits": rag_meta["hit_count"],
                "rag_sources": rag_meta["sources"],
                "rag_warnings": rag_bundle.warnings,
                "prompt_versions": get_prompt_versions(),
                "timings_ms": {"rag_retrieval": round(sum(rag_bundle.timings_ms.values()), 2)},
            }
            if task:
                task.status = "done"
                task.result = result
                task.completed_at = datetime.now(timezone.utc)
                db.commit()

            return result

        except Exception as e:
            logger.error("Outline generation failed", error=str(e), trace_id=trace_id)
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
            raise self.retry(exc=e)


@shared_task(bind=True)
def rewrite_chapter_task(self, chapter_id: str):
    trace_id = set_trace_id()
    logger.info("Starting chapter rewrite", trace_id=trace_id, chapter_id=chapter_id)

    with Session(sync_engine) as db:
        task = db.execute(
            select(GenerationTask).where(GenerationTask.id == self.request.id)
        ).scalar_one_or_none()

        if task:
            task.status = "running"
            task.started_at = datetime.now(timezone.utc)
            db.commit()

        try:
            chapter = db.execute(select(Chapter).where(Chapter.id == chapter_id)).scalar_one()
            novel = db.execute(select(Novel).where(Novel.id == chapter.novel_id)).scalar_one()
            style = novel.style_config or {}
            target_words = chapter.word_count or style.get("words_per_chapter", 3000)

            result = asyncio.run(
                _run_rewrite(db, novel, chapter, target_words, task_id=str(task.id if task else ""))
            )

            if task:
                task.status = "done"
                task.result = result
                task.completed_at = datetime.now(timezone.utc)
                db.commit()

            return result

        except Exception as e:
            logger.error("Rewrite failed", error=str(e), trace_id=trace_id)
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
            raise self.retry(exc=e)


async def _run_rewrite(
    db: Session,
    novel,
    chapter: Chapter,
    target_words: int,
    task_id: str = "",
) -> dict:
    outline_summary = ""
    if chapter.outline_id:
        outline = db.execute(select(Outline).where(Outline.id == chapter.outline_id)).scalar_one_or_none()
        if outline:
            outline_summary = f"Title: {outline.title}\nSummary: {outline.summary or ''}"

    previous_rows = db.execute(
        select(Chapter)
        .where(Chapter.novel_id == novel.id, Chapter.chapter_number < chapter.chapter_number)
        .order_by(Chapter.chapter_number.desc())
        .limit(3)
    ).scalars().all()
    previous_context = "\n\n".join(
        f"Chapter {ch.chapter_number} {ch.title}\n{(ch.content or '')[-500:]}"
        for ch in reversed(previous_rows)
    )

    characters = db.execute(
        select(Character).where(Character.novel_id == novel.id)
    ).scalars().all()
    character_context = "\n".join(
        f"{c.name}({c.role}): " + "; ".join(f"{k}: {v}" for k, v in (c.profile or {}).items())
        for c in characters
    )

    description = (
        f"请在保留核心情节、人物动机和连续性的基础上重写章节《{chapter.title}》。"
        "改善节奏、画面感和对白自然度，不要改变章节编号。\n\n"
        f"原文：\n{(chapter.content or '')[:4000]}"
    )
    rag_bundle = SyncRagContextService(db).build_chapter_context(
        novel_id=str(novel.id),
        outline_summary=outline_summary,
        description=description,
        chapter_number=chapter.chapter_number,
    )
    rag_context = format_rag_context(rag_bundle)
    rag_meta = rag_bundle.metadata()

    r = redis.from_url(settings.redis_url)
    segments = []

    async def on_segment(stage: str, text: str, percent: float):
        segment_data = {"stage": stage, "text": text, "percent": percent}
        segments.append(segment_data)
        if task_id:
            try:
                r.publish(f"generation:{task_id}", json.dumps(segment_data, ensure_ascii=False))
            except Exception:
                pass

    content, word_count, tokens_used = await WritingAgent().generate(
        genre=novel.genre,
        tone=novel.style_config.get("tone", "hot-blooded"),
        pov=novel.style_config.get("pov", "third person"),
        words_per_chapter=target_words,
        style_instructions=novel.style_config.get("custom_instructions", ""),
        outline_summary=outline_summary,
        previous_context=previous_context,
        character_context=character_context,
        rag_context=rag_context,
        description=description,
        on_segment=on_segment,
    )

    chapter.content = content
    chapter.word_count = word_count
    chapter.status = "draft"
    chapter.generation_meta = {
        **(chapter.generation_meta or {}),
        "rewrite": {
            "tokens_used": tokens_used,
            "segments": len(segments),
            "rag_hits": rag_meta["hit_count"],
            "rag_sources": rag_meta["sources"],
            "rag_warnings": rag_bundle.warnings,
            "prompt_versions": get_prompt_versions(),
        },
    }
    try:
        chapter.embedding = await embed_query(f"{chapter.title}\n{content[:3000]}")
    except Exception:
        pass

    db.commit()
    db.refresh(chapter)

    if task_id:
        try:
            r.publish(f"generation:{task_id}", json.dumps(
                {"stage": "complete", "text": "", "percent": 100},
                ensure_ascii=False,
            ))
        except Exception:
            pass

    return {
        "chapter_id": str(chapter.id),
        "word_count": word_count,
        "tokens_used": tokens_used,
        "rag_hits": rag_meta["hit_count"],
        "rag_sources": rag_meta["sources"],
        "rag_warnings": rag_bundle.warnings,
        "timings_ms": {"rag_retrieval": round(sum(rag_bundle.timings_ms.values()), 2)},
    }


@shared_task
def check_scheduled_novels():
    """Celery Beat periodic task: scan novels with enabled schedules and trigger generation."""
    with Session(sync_engine) as db:
        novels = db.execute(select(Novel).where(Novel.status == "writing")).scalars().all()

        for novel in novels:
            schedule = novel.schedule_config or {}
            if schedule.get("enabled"):
                latest = db.execute(
                    select(Chapter.chapter_number)
                    .where(Chapter.novel_id == novel.id)
                    .order_by(Chapter.chapter_number.desc())
                    .limit(1)
                ).scalar() or 0

                task = GenerationTask(
                    novel_id=novel.id,
                    task_type="chapter",
                    status="queued",
                )
                db.add(task)
                db.commit()

                generate_chapter_task.apply_async(
                    args=[str(novel.id), None, latest + 1],
                    task_id=str(task.id),
                )
