from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.config import settings

# Convert postgresql:// to postgresql+asyncpg:// for async driver
async_db_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(async_db_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    access_token: str | None = Query(default=None),
):
    if not settings.access_token or settings.access_token == "change-me":
        return
    bearer_token = credentials.credentials if credentials else None
    if bearer_token != settings.access_token and access_token != settings.access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
