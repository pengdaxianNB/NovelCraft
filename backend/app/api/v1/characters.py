from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.character import CharacterCreate, CharacterUpdate, CharacterResponse
from app.services.character_service import CharacterService

router = APIRouter(tags=["characters"])


@router.get("/novels/{novel_id}/characters", response_model=list[CharacterResponse])
async def list_characters(novel_id: str, db: AsyncSession = Depends(get_db)):
    return await CharacterService(db).list_characters(novel_id)


@router.post("/novels/{novel_id}/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
async def create_character(novel_id: str, data: CharacterCreate, db: AsyncSession = Depends(get_db)):
    return await CharacterService(db).create_character(novel_id, data)


@router.get("/characters/{character_id}", response_model=CharacterResponse)
async def get_character(character_id: str, db: AsyncSession = Depends(get_db)):
    character = await CharacterService(db).get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.patch("/characters/{character_id}", response_model=CharacterResponse)
async def update_character(character_id: str, data: CharacterUpdate, db: AsyncSession = Depends(get_db)):
    character = await CharacterService(db).update_character(character_id, data)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(character_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await CharacterService(db).delete_character(character_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found")
