from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.novel import NovelCreate, NovelUpdate, NovelStyleUpdate, NovelResponse
from app.services.novel_service import NovelService

router = APIRouter(prefix="/novels", tags=["novels"])


@router.get("", response_model=list[NovelResponse])
async def list_novels(db: AsyncSession = Depends(get_db)):
    return await NovelService(db).list_novels()


@router.post("", response_model=NovelResponse, status_code=status.HTTP_201_CREATED)
async def create_novel(data: NovelCreate, db: AsyncSession = Depends(get_db)):
    return await NovelService(db).create_novel(data)


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(novel_id: str, db: AsyncSession = Depends(get_db)):
    novel = await NovelService(db).get_novel(novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return await NovelService(db)._to_response(novel)


@router.patch("/{novel_id}", response_model=NovelResponse)
async def update_novel(novel_id: str, data: NovelUpdate, db: AsyncSession = Depends(get_db)):
    novel = await NovelService(db).update_novel(novel_id, data)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return await NovelService(db)._to_response(novel)


@router.delete("/{novel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_novel(novel_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await NovelService(db).delete_novel(novel_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Novel not found")


@router.patch("/{novel_id}/style", response_model=NovelResponse)
async def update_style(novel_id: str, data: NovelStyleUpdate, db: AsyncSession = Depends(get_db)):
    novel = await NovelService(db).update_style(novel_id, data)
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")
    return await NovelService(db)._to_response(novel)
