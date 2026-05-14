from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.world_setting import WorldSetting
from app.schemas.world_setting import WorldSettingCreate, WorldSettingUpdate
from app.ai.rag.embedder import embed_query


class WorldSettingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_world_settings(self, novel_id: str) -> list[WorldSetting]:
        stmt = select(WorldSetting).where(WorldSetting.novel_id == novel_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_world_setting(self, setting_id: str) -> WorldSetting | None:
        stmt = select(WorldSetting).where(WorldSetting.id == setting_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_world_setting(
        self, novel_id: str, data: WorldSettingCreate
    ) -> WorldSetting:
        setting = WorldSetting(novel_id=novel_id, **data.model_dump())
        try:
            embed_text = f"[{setting.category}] {setting.title}: {setting.content}"
            setting.embedding = await embed_query(embed_text)
        except Exception:
            pass
        self.db.add(setting)
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def update_world_setting(
        self, setting_id: str, data: WorldSettingUpdate
    ) -> WorldSetting | None:
        setting = await self.get_world_setting(setting_id)
        if not setting:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            if v is not None:
                setattr(setting, k, v)
        try:
            embed_text = f"[{setting.category}] {setting.title}: {setting.content}"
            setting.embedding = await embed_query(embed_text)
        except Exception:
            pass
        await self.db.commit()
        await self.db.refresh(setting)
        return setting

    async def delete_world_setting(self, setting_id: str) -> bool:
        setting = await self.get_world_setting(setting_id)
        if not setting:
            return False
        await self.db.delete(setting)
        await self.db.commit()
        return True
