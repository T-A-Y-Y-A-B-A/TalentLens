from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_permission
from app.models.identity import User
from app.schemas.copilot import CopilotQueryRequest, CopilotQueryResponse
from app.services.copilot import query_copilot

router = APIRouter(prefix="/copilot", tags=["copilot"])

@router.post("/query", response_model=CopilotQueryResponse)
async def execute_copilot_query(
    request: CopilotQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("copilot", "use"))
):
    """
    Executes a natural language query against the candidate pool.
    Translates the query using LLM and returns matching candidates via semantic and structured search.
    """
    return await query_copilot(db, request, current_user)
