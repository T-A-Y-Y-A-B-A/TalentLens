from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.identity import User
from app.schemas.analytics import AnalyticsDashboardResponse
from app.services.analytics import get_dashboard_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/dashboard", response_model=AnalyticsDashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves aggregated analytics metrics for the current user's organization.
    """
    return await get_dashboard_analytics(db, current_user.org_id)
