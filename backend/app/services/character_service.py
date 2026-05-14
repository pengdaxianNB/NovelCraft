from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.character import Character
from app.schemas.character import CharacterCreate, CharacterUpdate
from app.ai.rag.embedder import embed_query


def _build_character_embed_text(name: str, role: str, profile: dict | None) -> str:
    profile_parts = [f"{k}: {v}" for k, v in (profile or {}).items()]
    return f"{name} ({role}): {'; '.join(profile_parts)}"


class CharacterService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_characters(self, novel_id: str) -> list[Character]:
        stmt = select(Character).where(Character.novel_id == novel_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_character(self, character_id: str) -> Character | None:
        stmt = select(Character).where(Character.id == character_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_character(self, novel_id: str, data: CharacterCreate) -> Character:
        character = Character(novel_id=novel_id, **data.model_dump())
        try:
            embed_text = _build_character_embed_text(character.name, character.role, character.profile)
            character.embedding = await embed_query(embed_text)
        except Exception:
            pass
        self.db.add(character)
        await self.db.commit()
        await self.db.refresh(character)
        return character

    async def update_character(self, character_id: str, data: CharacterUpdate) -> Character | None:
        character = await self.get_character(character_id)
        if not character:
            return None
        for k, v in data.model_dump(exclude_unset=True).items():
            if v is not None:
                setattr(character, k, v)
        try:
            embed_text = _build_character_embed_text(character.name, character.role, character.profile)
            character.embedding = await embed_query(embed_text)
        except Exception:
            pass
        await self.db.commit()
        await self.db.refresh(character)
        return character

    async def delete_character(self, character_id: str) -> bool:
        character = await self.get_character(character_id)
        if not character:
            return False
        await self.db.delete(character)
        await self.db.commit()
        return True
