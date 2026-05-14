from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.ai.agents.world_setting_agent import WorldSettingAgent
from app.schemas.world_setting import (
    WorldSettingConsistencyRequest,
    WorldSettingConsistencyResponse,
    WorldSettingCreate,
    WorldSettingResponse,
    WorldSettingUpdate,
)
from app.services.world_setting_service import WorldSettingService
from app.services.rag_context_service import (
    AsyncRagContextService,
    RagContextBundle,
    format_rag_context,
)

router = APIRouter(tags=["world-settings"])


@router.get("/novels/{novel_id}/world-settings", response_model=list[WorldSettingResponse])
async def list_world_settings(novel_id: str, db: AsyncSession = Depends(get_db)):
    return await WorldSettingService(db).list_world_settings(novel_id)


@router.post("/novels/{novel_id}/world-settings", response_model=WorldSettingResponse, status_code=status.HTTP_201_CREATED)
async def create_world_setting(novel_id: str, data: WorldSettingCreate, db: AsyncSession = Depends(get_db)):
    return await WorldSettingService(db).create_world_setting(novel_id, data)


@router.post(
    "/novels/{novel_id}/world-settings/check",
    response_model=WorldSettingConsistencyResponse,
)
async def check_world_setting(
    novel_id: str,
    data: WorldSettingConsistencyRequest,
    db: AsyncSession = Depends(get_db),
):
    rag_bundle = None
    try:
        rag_bundle = await AsyncRagContextService(db).build_world_setting_context(
            novel_id=novel_id,
            category=data.category,
            title=data.title,
            content=data.content,
        )
    except Exception as exc:
        await db.rollback()
        rag_bundle = RagContextBundle(
            query=f"{data.category} {data.title}",
            warnings=[f"rag retrieval failed: {exc}"],
        )

    try:
        review = await WorldSettingAgent().check_consistency(
            category=data.category,
            title=data.title,
            content=data.content,
            rag_context=format_rag_context(rag_bundle),
        )
    except Exception as exc:
        review = {
            "passed": True,
            "issues": [],
            "summary": f"AI consistency check is temporarily unavailable: {exc}",
        }

    return WorldSettingConsistencyResponse(
        passed=bool(review.get("passed", True)),
        issues=review.get("issues") or [],
        summary=review.get("summary") or "",
        rag_hits=[
            {"source": hit.source, "title": hit.title, "metadata": hit.metadata}
            for hit in rag_bundle.hits
        ],
        timings_ms={"rag_retrieval": round(sum(rag_bundle.timings_ms.values()), 2)},
    )


@router.get("/world-settings/{setting_id}", response_model=WorldSettingResponse)
async def get_world_setting(setting_id: str, db: AsyncSession = Depends(get_db)):
    setting = await WorldSettingService(db).get_world_setting(setting_id)
    if not setting:
        raise HTTPException(status_code=404, detail="World setting not found")
    return setting


@router.patch("/world-settings/{setting_id}", response_model=WorldSettingResponse)
async def update_world_setting(setting_id: str, data: WorldSettingUpdate, db: AsyncSession = Depends(get_db)):
    setting = await WorldSettingService(db).update_world_setting(setting_id, data)
    if not setting:
        raise HTTPException(status_code=404, detail="World setting not found")
    return setting


@router.delete("/world-settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_world_setting(setting_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await WorldSettingService(db).delete_world_setting(setting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="World setting not found")
