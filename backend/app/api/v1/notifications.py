import uuid
from typing import List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.core.dependencies import get_db, get_current_candidate
from app.models.support import Notification
from pydantic import BaseModel

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationRead(BaseModel):
    id: uuid.UUID
    type: str
    channel: str
    payload: Dict[str, Any]
    read_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[NotificationRead])
async def get_notifications(
    db: AsyncSession = Depends(get_db),
    current_candidate = Depends(get_current_candidate)
):
    res = await db.execute(
        select(Notification)
        .where(Notification.recipient_id == str(current_candidate.id))
        .order_by(Notification.created_at.desc())
    )
    return res.scalars().all()
