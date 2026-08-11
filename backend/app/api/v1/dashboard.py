from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import get_db, require_permission
from app.models.identity import User
from app.services.dashboard import get_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardStatsResponse(BaseModel):
    active_jobs: int
    total_candidates: int
    interviews_today: int
    new_applications_24h: int


@router.get("/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("organization", "read")),
):
    """
    Returns the four headline stats for the HR dashboard.
    All counts are scoped to the current user's org_id — never client-supplied.
    """
    return await get_dashboard_stats(db, current_user.org_id)
