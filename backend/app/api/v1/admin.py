from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from typing import List
import structlog

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User, Organization, UserRole
from app.models.recruitment import Job, JobStatus
from app.models.candidate import Candidate
from app.models.ai import AIUsageLog
from app.models.support import AuditLog
from app.schemas.admin import (
    AdminPlatformStats, AdminOrganizationOut, 
    AdminAuditLogOut, AdminUsageLogOut
)

router = APIRouter(prefix="/admin", tags=["admin"])
logger = structlog.get_logger()

async def get_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires super admin privileges"
        )
    return current_user

@router.get("/stats", response_model=AdminPlatformStats)
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_super_admin)
):
    total_orgs = await db.scalar(select(func.count(Organization.id)))
    total_users = await db.scalar(select(func.count(User.id)))
    total_candidates = await db.scalar(select(func.count(Candidate.id)))
    total_ai_calls = await db.scalar(select(func.count(AIUsageLog.id)))
    active_jobs = await db.scalar(select(func.count(Job.id)).where(Job.status == JobStatus.OPEN))
    
    return AdminPlatformStats(
        total_organizations=total_orgs or 0,
        total_users=total_users or 0,
        total_candidates=total_candidates or 0,
        total_ai_calls=total_ai_calls or 0,
        active_jobs=active_jobs or 0
    )

@router.get("/organizations", response_model=List[AdminOrganizationOut])
async def list_organizations(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_super_admin)
):
    # Use explicit aggregate subqueries or count(distinct) to avoid row multiplication
    # Note: Using count(distinct) here for simplicity and safety as per user feedback
    stmt = (
        select(
            Organization,
            func.count(distinct(User.id)).label("users_count"),
            func.count(distinct(Job.id)).label("active_jobs_count")
        )
        .outerjoin(User, User.org_id == Organization.id)
        .outerjoin(Job, (Job.org_id == Organization.id) & (Job.status == JobStatus.OPEN))
        .group_by(Organization.id)
        .order_by(Organization.created_at.desc())
    )
    
    result = await db.execute(stmt)
    rows = result.all()
    
    output = []
    for org, u_count, j_count in rows:
        output.append(AdminOrganizationOut(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            users_count=u_count,
            active_jobs_count=j_count
        ))
    
    return output

@router.get("/audit_logs", response_model=List[AdminAuditLogOut])
async def list_audit_logs(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_super_admin)
):
    # Note: In a production DB, ensure an index exists on created_at to avoid full table scans.
    stmt = (
        select(AuditLog, Organization.name.label("org_name"), User.email.label("actor_email"))
        .outerjoin(Organization, Organization.id == AuditLog.tenant_id)
        .outerjoin(User, User.id == AuditLog.actor_id)
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    output = []
    for log, org_name, actor_email in rows:
        output.append(AdminAuditLogOut(
            id=log.id,
            created_at=log.created_at,
            org_name=org_name or "System",
            actor_email=actor_email or "unknown",
            action=log.action,
            resource_id=str(log.entity_id),
            status="success" # Assuming success for now as there's no status column in AuditLog
        ))
    return output

@router.get("/usage_logs", response_model=List[AdminUsageLogOut])
async def list_usage_logs(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_super_admin)
):
    # Note: In a production DB, ensure an index exists on created_at to avoid full table scans.
    stmt = (
        select(AIUsageLog, Organization.name.label("org_name"))
        .outerjoin(Organization, Organization.id == AIUsageLog.org_id)
        .order_by(AIUsageLog.created_at.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    output = []
    for log, org_name in rows:
        output.append(AdminUsageLogOut(
            id=log.id,
            created_at=log.created_at,
            org_name=org_name or "System",
            endpoint=log.endpoint,
            total_tokens=log.total_tokens,
            latency_ms=log.latency_ms,
            candidates_matched=log.candidates_matched
        ))
    return output
