from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.debug)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.router import router as v1_router
app.include_router(v1_router)


@app.get("/health")
async def health():
    import redis
    from sqlalchemy import create_engine, text
    health_status = {"status": "ok", "service": settings.app_name}
    # Check DB
    try:
        sync_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "ok"
    except Exception as e:
        health_status["database"] = str(e)
    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        health_status["redis"] = "ok"
    except Exception as e:
        health_status["redis"] = str(e)
    return health_status
