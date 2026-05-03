from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.chapter import ChapterUpdate, ChapterResponse
from app.services.chapter_service import ChapterService

router = APIRouter(tags=["chapters"])


@router.get("/novels/{novel_id}/chapters", response_model=list[ChapterResponse])
async def list_chapters(novel_id: str, db: AsyncSession = Depends(get_db)):
    return await ChapterService(db).list_chapters(novel_id)


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_chapter(chapter_id: str, db: AsyncSession = Depends(get_db)):
    chapter = await ChapterService(db).get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.patch("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_chapter(chapter_id: str, data: ChapterUpdate, db: AsyncSession = Depends(get_db)):
    chapter = await ChapterService(db).update_chapter(chapter_id, **data.model_dump(exclude_unset=True))
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.post("/chapters/{chapter_id}/publish", response_model=ChapterResponse)
async def publish_chapter(chapter_id: str, db: AsyncSession = Depends(get_db)):
    chapter = await ChapterService(db).publish(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.post("/chapters/{chapter_id}/rewrite", status_code=status.HTTP_202_ACCEPTED)
async def rewrite_chapter(chapter_id: str, db: AsyncSession = Depends(get_db)):
    chapter = await ChapterService(db).get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    # Will be implemented when Celery tasks are ready
    return {"message": "Rewrite triggered", "chapter_id": chapter_id}
