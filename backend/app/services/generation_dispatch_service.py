import uuid as uuid_module

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generation_task import GenerationTask
from app.services.chapter_service import ChapterService
from app.services.novel_service import NovelService
from app.tasks.celery_app import celery_app


class GenerationDispatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def dispatch_outline(
        self, novel_id: str, level: str, parent_id: str = "", count: int = 5,
    ) -> dict:
        novel = await NovelService(self.db).get_novel(novel_id)
        if not novel:
            raise ValueError(f"小说 {novel_id} 不存在")

        parent = parent_id if parent_id else None
        task = GenerationTask(
            id=uuid_module.uuid4(),
            novel_id=novel_id,
            task_type="outline",
            target_id=parent,
            status="queued",
        )
        self.db.add(task)
        await self.db.commit()

        celery_app.send_task(
            "app.tasks.generation_tasks.generate_outline_task",
            args=[novel_id, level, parent, count],
            task_id=str(task.id),
        )
        return {"task_id": str(task.id), "status": "queued"}

    async def dispatch_chapter(
        self,
        novel_id: str,
        outline_id: str = "",
        chapter_number: int = 0,
        words_per_chapter: int | None = None,
        description: str = "",
    ) -> dict:
        novel = await NovelService(self.db).get_novel(novel_id)
        if not novel:
            raise ValueError(f"小说 {novel_id} 不存在")

        actual_chapter = chapter_number
        if actual_chapter < 1:
            actual_chapter = await ChapterService(self.db).get_latest_chapter_number(novel_id) + 1

        oid = outline_id if outline_id else None

        task = GenerationTask(
            id=uuid_module.uuid4(),
            novel_id=novel_id,
            task_type="chapter",
            target_id=oid,
            status="queued",
        )
        self.db.add(task)
        await self.db.commit()

        celery_app.send_task(
            "app.tasks.generation_tasks.generate_chapter_task",
            args=[novel_id, oid, actual_chapter, words_per_chapter, description or None],
            task_id=str(task.id),
        )
        return {"task_id": str(task.id), "chapter_number": actual_chapter, "status": "queued"}

    async def dispatch_rewrite(self, chapter_id: str) -> dict:
        chapter = await ChapterService(self.db).get_chapter(chapter_id)
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")

        task = GenerationTask(
            id=uuid_module.uuid4(),
            novel_id=chapter.novel_id,
            task_type="rewrite",
            target_id=chapter.id,
            status="queued",
        )
        self.db.add(task)
        await self.db.commit()

        celery_app.send_task(
            "app.tasks.generation_tasks.rewrite_chapter_task",
            args=[chapter_id],
            task_id=str(task.id),
        )
        return {"task_id": str(task.id), "chapter_id": chapter_id, "status": "queued"}
