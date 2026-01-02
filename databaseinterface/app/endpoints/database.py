from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.dependencies import get_db

router = APIRouter()

@router.get("/query")
async def execute_query(
    query: str,
    db: AsyncSession = Depends(get_db)
):
    """Execute a raw SQL query (use with caution)"""
    try:
        result = await db.execute(text(query))
        await db.commit()
        return {"status": "success", "result": str(result)}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/health")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    """Check database connection health"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "connected", "database": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

