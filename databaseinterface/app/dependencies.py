from sqlalchemy.ext.asyncio import AsyncSession
from app.utils import async_session

async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

