import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.api.deps import get_db
from app.ai.agents.review_agent import ReviewAgent
from app.models.chapter import Chapter
from app.models.character import Character
from app.models.novel import Novel
from app.models.world_setting import WorldSetting
from app.schemas.chapter import ChapterReviewRequest, ChapterReviewResponse, ChapterUpdate, ChapterResponse
from app.services.chapter_service import ChapterService
from app.services.generation_dispatch_service import GenerationDispatchService
from app.services.rag_context_service import AsyncRagContextService, format_rag_context

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


@router.post("/chapters/{chapter_id}/review", response_model=ChapterReviewResponse)
async def review_chapter(
    chapter_id: str,
    data: ChapterReviewRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    chapter = await ChapterService(db).get_chapter(chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    novel = (
        await db.execute(select(Novel).where(Novel.id == chapter.novel_id))
    ).scalar_one_or_none()
    if not novel:
        raise HTTPException(status_code=404, detail="Novel not found")

    content = data.content if data and data.content is not None else (chapter.content or "")
    rag_bundle = await AsyncRagContextService(db).build_review_context(
        novel_id=str(chapter.novel_id),
        chapter_content=content,
        chapter_number=chapter.chapter_number,
    )

    character_rows = (
        await db.execute(select(Character).where(Character.novel_id == chapter.novel_id).limit(12))
    ).scalars().all()
    character_context = "\n".join(
        f"{c.name}({c.role}): "
        + "; ".join(f"{k}: {v}" for k, v in (c.profile or {}).items())
        for c in character_rows
    )

    world_rows = (
        await db.execute(select(WorldSetting).where(WorldSetting.novel_id == chapter.novel_id).limit(12))
    ).scalars().all()
    world_context = "\n".join(f"[{w.category}] {w.title}: {w.content}" for w in world_rows)

    previous_rows = (
        await db.execute(
            select(Chapter)
            .where(Chapter.novel_id == chapter.novel_id, Chapter.chapter_number < chapter.chapter_number)
            .order_by(Chapter.chapter_number.desc())
            .limit(3)
        )
    ).scalars().all()
    previous_context = "\n\n".join(
        f"Chapter {ch.chapter_number} {ch.title}\n{(ch.content or '')[-500:]}"
        for ch in reversed(previous_rows)
    )

    review = await ReviewAgent().review(
        chapter_title=chapter.title,
        chapter_content=content,
        words_per_chapter=(novel.style_config or {}).get("words_per_chapter", 3000),
        style_config=json.dumps(novel.style_config or {}, ensure_ascii=False),
        character_context=character_context,
        world_context=world_context + "\n\n" + format_rag_context(rag_bundle),
        previous_context=previous_context,
    )
    return ChapterReviewResponse(
        passed=bool(review.get("passed", True)),
        issues=review.get("issues") or [],
        summary=review.get("summary") or "",
        rag_hits=[
            {"source": hit.source, "title": hit.title, "metadata": hit.metadata}
            for hit in rag_bundle.hits
        ],
        timings_ms={"rag_retrieval": round(sum(rag_bundle.timings_ms.values()), 2)},
    )


@router.post("/chapters/{chapter_id}/rewrite", status_code=status.HTTP_202_ACCEPTED)
async def rewrite_chapter(chapter_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await GenerationDispatchService(db).dispatch_rewrite(chapter_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Chapter not found")
