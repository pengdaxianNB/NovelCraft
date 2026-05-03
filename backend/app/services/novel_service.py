from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.novel import Novel
from app.models.chapter import Chapter
from app.schemas.novel import NovelCreate, NovelUpdate, NovelStyleUpdate, NovelResponse


class NovelService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_novels(self) -> list[NovelResponse]:
        stmt = select(Novel).order_by(Novel.updated_at.desc())
        result = await self.db.execute(stmt)
        novels = result.scalars().all()
        return [await self._to_response(n) for n in novels]

    async def get_novel(self, novel_id: str) -> Novel | None:
        stmt = select(Novel).where(Novel.id == novel_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_novel(self, data: NovelCreate) -> Novel:
        novel = Novel(
            title=data.title,
            genre=data.genre,
            synopsis=data.synopsis,
            style_config=data.style_config.model_dump(),
            schedule_config=data.schedule_config.model_dump(),
        )
        self.db.add(novel)
        await self.db.commit()
        await self.db.refresh(novel)
        return novel

    async def update_novel(self, novel_id: str, data: NovelUpdate) -> Novel | None:
        novel = await self.get_novel(novel_id)
        if not novel:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(novel, k, v)
        await self.db.commit()
        await self.db.refresh(novel)
        return novel

    async def update_style(self, novel_id: str, data: NovelStyleUpdate) -> Novel | None:
        novel = await self.get_novel(novel_id)
        if not novel:
            return None
        style = dict(novel.style_config)
        style.update(data.model_dump(exclude_unset=True))
        novel.style_config = style
        await self.db.commit()
        await self.db.refresh(novel)
        return novel

    async def delete_novel(self, novel_id: str) -> bool:
        novel = await self.get_novel(novel_id)
        if not novel:
            return False
        await self.db.delete(novel)
        await self.db.commit()
        return True

    async def _to_response(self, novel: Novel) -> NovelResponse:
        ch_count = await self.db.scalar(
            select(func.count(Chapter.id)).where(Chapter.novel_id == novel.id)
        )
        pub_count = await self.db.scalar(
            select(func.count(Chapter.id)).where(
                Chapter.novel_id == novel.id, Chapter.status == "published"
            )
        )
        return NovelResponse(
            id=str(novel.id),
            title=novel.title,
            genre=novel.genre,
            synopsis=novel.synopsis,
            style_config=novel.style_config,
            schedule_config=novel.schedule_config,
            status=novel.status,
            created_at=novel.created_at,
            updated_at=novel.updated_at,
            chapter_count=ch_count or 0,
            published_count=pub_count or 0,
        )
