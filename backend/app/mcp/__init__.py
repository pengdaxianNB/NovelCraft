from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import async_session


@asynccontextmanager
async def get_mcp_db():
    async with async_session() as session:
        yield session
