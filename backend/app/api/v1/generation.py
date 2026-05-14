from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
from app.api.deps import get_db
from app.schemas.generation import GenerateOutlineRequest, GenerateChapterRequest, GenerationTaskResponse
from app.models.generation_task import GenerationTask
from app.services.generation_dispatch_service import GenerationDispatchService
import json
import asyncio
import redis.asyncio as aioredis
from app.config import settings

router = APIRouter(tags=["generation"])


@router.post("/novels/{novel_id}/generate/outline", status_code=status.HTTP_202_ACCEPTED)
async def generate_outline(novel_id: str, data: GenerateOutlineRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await GenerationDispatchService(db).dispatch_outline(
            novel_id=novel_id,
            level=data.level,
            parent_id=data.parent_id or "",
            count=data.count,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/novels/{novel_id}/generate/chapter", status_code=status.HTTP_202_ACCEPTED)
async def generate_chapter(novel_id: str, data: GenerateChapterRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await GenerationDispatchService(db).dispatch_chapter(
            novel_id=novel_id,
            outline_id=data.outline_id or "",
            chapter_number=data.chapter_number or 0,
            words_per_chapter=data.words_per_chapter,
            description=data.description or "",
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/generation/tasks", response_model=list[GenerationTaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    stmt = select(GenerationTask).order_by(GenerationTask.created_at.desc()).limit(50)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/generation/tasks/{task_id}", response_model=GenerationTaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    stmt = select(GenerationTask).where(GenerationTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/generation/tasks/{task_id}/cancel")
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    stmt = select(GenerationTask).where(GenerationTask.id == task_id)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = "cancelled"
    await db.commit()
    return {"task_id": task_id, "status": "cancelled"}


@router.get("/generation/stream/{task_id}")
async def stream_generation(task_id: str):
    async def event_generator():
        r = aioredis.from_url(settings.redis_url)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"generation:{task_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    if isinstance(data, bytes):
                        data = data.decode("utf-8")
                    yield {"event": "progress", "data": data}
        finally:
            await pubsub.unsubscribe(f"generation:{task_id}")
            await r.close()

    return EventSourceResponse(event_generator())
