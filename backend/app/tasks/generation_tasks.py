import asyncio
import json
from datetime import datetime, timezone
from celery import shared_task
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config import settings
from app.models.novel import Novel
from app.models.chapter import Chapter
from app.models.outline import Outline
from app.models.generation_task import GenerationTask
from app.ai.agents.writing_agent import WritingAgent
from app.ai.agents.outline_agent import OutlineAgent
from app.ai.agents.review_agent import ReviewAgent
from app.utils.logging import get_logger, set_trace_id

logger = get_logger(__name__)
sync_engine = create_engine(settings.database_url)


@shared_task(bind=True)
def generate_chapter_task(self, novel_id: str, outline_id: str | None = None,
                          chapter_number: int | None = None, words_override: int | None = None):
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

            result = asyncio.get_event_loop().run_until_complete(
                _run_generation(db, novel, outline_id, chapter_number or 1, words)
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


async def _run_generation(db: Session, novel, outline_id, chapter_number: int, words: int) -> dict:
    agent = WritingAgent()
    segments = []

    async def on_segment(stage: str, text: str, percent: float):
        segments.append({"stage": stage, "text": text})

    content, word_count, tokens_used = await agent.generate(
        genre=novel.genre,
        tone=novel.style_config.get("tone", "热血"),
        pov=novel.style_config.get("pov", "第三人称"),
        words_per_chapter=words,
        style_instructions=novel.style_config.get("custom_instructions", ""),
        outline_summary="",
        previous_context="",
        character_context="",
        rag_context="",
        on_segment=on_segment,
    )

    chapter = Chapter(
        novel_id=novel.id,
        outline_id=outline_id,
        chapter_number=chapter_number,
        title=f"第{chapter_number}章",
        content=content,
        word_count=word_count,
        status="draft",
        generation_meta={"tokens_used": tokens_used, "segments": len(segments)},
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    return {"chapter_id": str(chapter.id), "word_count": word_count, "tokens_used": tokens_used}


@shared_task
def generate_outline_task(novel_id: str, level: str, parent_id: str | None, count: int):
    trace_id = set_trace_id()
    logger.info("Starting outline generation", trace_id=trace_id, novel_id=novel_id)

    with Session(sync_engine) as db:
        novel = db.execute(select(Novel).where(Novel.id == novel_id)).scalar_one()
        agent = OutlineAgent()
        outlines = asyncio.get_event_loop().run_until_complete(
            agent.generate(
                genre=novel.genre,
                level=level,
                parent_title="",
                count=count,
                world_context="",
                character_context="",
                existing_outlines="",
            )
        )
        for i, o in enumerate(outlines):
            outline = Outline(
                novel_id=novel_id,
                level=level,
                parent_id=parent_id,
                sequence=i,
                title=o.get("title", f"{level} {i+1}"),
                summary=o.get("summary", ""),
            )
            db.add(outline)
        db.commit()

    return {"outlines_created": len(outlines)}


@shared_task
def check_scheduled_novels():
    """Celery Beat periodic task: scan novels with enabled schedules and trigger generation."""
    with Session(sync_engine) as db:
        novels = db.execute(
            select(Novel).where(Novel.status == "writing")
        ).scalars().all()

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
