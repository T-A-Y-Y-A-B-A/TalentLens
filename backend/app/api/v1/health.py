from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()

@router.get("/")
async def health_check():
    return {"status": "ok", "service": "talentlens-backend"}

@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        # Check DB connection
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "db": "connected"}
    except Exception as e:
        return {"status": "not_ready", "db": "disconnected", "error": str(e)}
