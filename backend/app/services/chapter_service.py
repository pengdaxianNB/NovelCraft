from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.chapter import Chapter


class ChapterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_chapters(self, novel_id: str) -> list[Chapter]:
        stmt = (
            select(Chapter)
            .where(Chapter.novel_id == novel_id)
            .order_by(Chapter.chapter_number)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_chapter(self, chapter_id: str) -> Chapter | None:
        stmt = select(Chapter).where(Chapter.id == chapter_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_chapter(self, chapter_id: str, **kwargs) -> Chapter | None:
        chapter = await self.get_chapter(chapter_id)
        if not chapter:
            return None
        for k, v in kwargs.items():
            if v is not None and hasattr(chapter, k):
                setattr(chapter, k, v)
        if "content" in kwargs and kwargs["content"]:
            chapter.word_count = len(kwargs["content"])
        await self.db.commit()
        await self.db.refresh(chapter)
        return chapter

    async def publish(self, chapter_id: str) -> Chapter | None:
        return await self.update_chapter(chapter_id, status="published")

    async def get_latest_chapter_number(self, novel_id: str) -> int:
        stmt = (
            select(Chapter.chapter_number)
            .where(Chapter.novel_id == novel_id)
            .order_by(Chapter.chapter_number.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        num = result.scalar()
        return num or 0
