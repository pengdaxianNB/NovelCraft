from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.outline import OutlineCreate, OutlineUpdate, OutlineReorder, OutlineResponse
from app.services.outline_service import OutlineService

router = APIRouter(tags=["outlines"])


@router.get("/novels/{novel_id}/outlines", response_model=list[OutlineResponse])
async def list_outlines(novel_id: str, db: AsyncSession = Depends(get_db)):
    return await OutlineService(db).list_outlines(novel_id)


@router.post("/novels/{novel_id}/outlines", response_model=OutlineResponse, status_code=status.HTTP_201_CREATED)
async def create_outline(novel_id: str, data: OutlineCreate, db: AsyncSession = Depends(get_db)):
    outline = await OutlineService(db).create_outline(novel_id, data)
    return outline


@router.get("/outlines/{outline_id}", response_model=OutlineResponse)
async def get_outline(outline_id: str, db: AsyncSession = Depends(get_db)):
    outline = await OutlineService(db).get_outline(outline_id)
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")
    return outline


@router.patch("/outlines/{outline_id}", response_model=OutlineResponse)
async def update_outline(outline_id: str, data: OutlineUpdate, db: AsyncSession = Depends(get_db)):
    outline = await OutlineService(db).update_outline(outline_id, data)
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")
    return outline


@router.delete("/outlines/{outline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_outline(outline_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await OutlineService(db).delete_outline(outline_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Outline not found")


@router.patch("/outlines/{outline_id}/reorder", response_model=OutlineResponse)
async def reorder_outline(outline_id: str, data: OutlineReorder, db: AsyncSession = Depends(get_db)):
    outline = await OutlineService(db).reorder(outline_id, data.new_sequence, data.new_parent_id)
    if not outline:
        raise HTTPException(status_code=404, detail="Outline not found")
    return outline
