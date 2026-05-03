from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.outline import Outline
from app.schemas.outline import OutlineCreate, OutlineUpdate, OutlineResponse


class OutlineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_outlines(self, novel_id: str) -> list[OutlineResponse]:
        stmt = (
            select(Outline)
            .where(Outline.novel_id == novel_id)
            .order_by(Outline.sequence)
        )
        result = await self.db.execute(stmt)
        outlines = result.scalars().all()
        return self._build_tree(outlines)

    async def get_outline(self, outline_id: str) -> Outline | None:
        stmt = select(Outline).where(Outline.id == outline_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_outline(
        self, novel_id: str, data: OutlineCreate
    ) -> Outline:
        outline = Outline(novel_id=novel_id, **data.model_dump())
        self.db.add(outline)
        await self.db.commit()
        await self.db.refresh(outline)
        return outline

    async def update_outline(
        self, outline_id: str, data: OutlineUpdate
    ) -> Outline | None:
        outline = await self.get_outline(outline_id)
        if not outline:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            if v is not None:
                setattr(outline, k, v)
        await self.db.commit()
        await self.db.refresh(outline)
        return outline

    async def delete_outline(self, outline_id: str) -> bool:
        outline = await self.get_outline(outline_id)
        if not outline:
            return False
        await self.db.delete(outline)
        await self.db.commit()
        return True

    async def reorder(
        self,
        outline_id: str,
        new_sequence: int,
        new_parent_id: str | None = None,
    ) -> Outline | None:
        outline = await self.get_outline(outline_id)
        if not outline:
            return None
        outline.sequence = new_sequence
        if new_parent_id is not None:
            outline.parent_id = new_parent_id
        await self.db.commit()
        await self.db.refresh(outline)
        return outline

    def _build_tree(self, outlines: list[Outline]) -> list[OutlineResponse]:
        lookup: dict[str, OutlineResponse] = {}
        roots: list[OutlineResponse] = []

        for o in outlines:
            item = OutlineResponse(
                id=str(o.id),
                novel_id=str(o.novel_id),
                level=o.level,
                parent_id=str(o.parent_id) if o.parent_id else None,
                sequence=o.sequence,
                title=o.title,
                summary=o.summary,
                status=o.status,
                children=[],
                created_at=o.created_at,
                updated_at=o.updated_at,
            )
            lookup[item.id] = item

        for o in outlines:
            item = lookup[str(o.id)]
            if o.parent_id and str(o.parent_id) in lookup:
                lookup[str(o.parent_id)].children.append(item)
            else:
                roots.append(item)

        return roots
