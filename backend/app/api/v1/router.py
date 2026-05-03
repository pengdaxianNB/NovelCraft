from fastapi import APIRouter
from app.api.v1.novels import router as novels_router
from app.api.v1.chapters import router as chapters_router
from app.api.v1.characters import router as characters_router
from app.api.v1.world_settings import router as world_settings_router
from app.api.v1.outlines import router as outlines_router
from app.api.v1.generation import router as generation_router
from app.api.v1.rag import router as rag_router

router = APIRouter(prefix="/api/v1")

router.include_router(novels_router)
router.include_router(chapters_router)
router.include_router(characters_router)
router.include_router(world_settings_router)
router.include_router(outlines_router)
router.include_router(generation_router)
router.include_router(rag_router)
