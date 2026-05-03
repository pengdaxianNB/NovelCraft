from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.world_setting import WorldSettingCreate, WorldSettingUpdate, WorldSettingResponse
from app.services.world_setting_service import WorldSettingService

router = APIRouter(tags=["world-settings"])


@router.get("/novels/{novel_id}/world-settings", response_model=list[WorldSettingResponse])
async def list_world_settings(novel_id: str, db: AsyncSession = Depends(get_db)):
    return await WorldSettingService(db).list_world_settings(novel_id)


@router.post("/novels/{novel_id}/world-settings", response_model=WorldSettingResponse, status_code=status.HTTP_201_CREATED)
async def create_world_setting(novel_id: str, data: WorldSettingCreate, db: AsyncSession = Depends(get_db)):
    return await WorldSettingService(db).create_world_setting(novel_id, data)


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
