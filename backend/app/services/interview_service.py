"""
Interview service layer — delete and related helpers.

Interview has no direct org_id column; org scoping is always through
Application -> Job.org_id (verified during research/planning phase).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException

from app.core.security import enforce_role
from app.models.interview import Interview
from app.models.application import Application
from app.models.recruitment import Job


async def delete_interview(
    db: AsyncSession,
    interview_id: uuid.UUID,
    org_id: uuid.UUID,
    actor_role: str,
) -> None:
    """
    Soft-delete an interview.

    RBAC: recruiter or hr_manager only.
    Org scoping: Interview → Application → Job.org_id (Interview has no direct org_id).
    Returns 404 for cross-org attempts — never 403 — to avoid resource enumeration.
    Sets deleted_at = now() AND status = "cancelled" (backward-compatible with status checks).
    """
    enforce_role(actor_role, "interviews", "delete")

    res = await db.execute(
        select(Interview)
        .join(Application, Interview.application_id == Application.id)
        .join(Job, Application.job_id == Job.id)
        .options(
            joinedload(Interview.application).joinedload(Application.candidate),
            joinedload(Interview.application).joinedload(Application.job),
        )
        .where(Interview.id == interview_id)
        .where(Job.org_id == org_id)
        .where(Interview.deleted_at.is_(None))
    )
    interview = res.scalars().first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    now = datetime.now(timezone.utc)
    interview.deleted_at = now
    interview.status = "cancelled"

    await db.commit()
