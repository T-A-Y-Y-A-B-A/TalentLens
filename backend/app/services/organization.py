import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.identity import User, Organization, UserRole, RefreshToken
from app.models.recruitment import Job
from app.models.support import AuditLog
from app.core.security import enforce_role
from app.schemas.organization import OrganizationUpdate


def _create_audit_log(
    db: AsyncSession,
    org_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    diff: dict,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None
):
    audit = AuditLog(
        org_id=org_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        diff=diff,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id
    )
    db.add(audit)


async def create_organization(db: AsyncSession, name: str, slug_suffix: Optional[str] = None) -> Organization:
    from sqlalchemy.exc import IntegrityError
    
    base_slug = name.lower().replace(" ", "-")
    slug = f"{base_slug}-{slug_suffix}" if slug_suffix else base_slug
    org = Organization(name=name, slug=slug)
    db.add(org)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Organization name is already taken. Please choose another one.")
    return org


async def get_organization(db: AsyncSession, org_id: uuid.UUID, current_user: User) -> Organization:
    if current_user.org_id != org_id and not current_user.is_platform_admin:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalars().first()
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return org


async def update_organization(
    db: AsyncSession, 
    org_id: uuid.UUID, 
    data: OrganizationUpdate, 
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None
) -> Organization:
    enforce_role(current_user.role.value, "organizations", "update")
    
    if current_user.org_id != org_id and not current_user.is_platform_admin:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    before_state = {"name": org.name, "plan": org.plan}
    after_state = {}
    
    if data.name is not None:
        org.name = data.name
        after_state["name"] = data.name
    if data.plan is not None:
        org.plan = data.plan
        after_state["plan"] = data.plan
        
    if after_state:
        _create_audit_log(
            db=db,
            org_id=org_id,
            actor_id=current_user.id,
            action="org_update",
            entity_type="organization",
            entity_id=org_id,
            diff={"before": {k: before_state[k] for k in after_state}, "after": after_state},
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id
        )
        await db.commit()
        await db.refresh(org)
        
    return org


async def list_organization_users(db: AsyncSession, org_id: uuid.UUID, current_user: User) -> List[User]:
    if current_user.org_id != org_id and not current_user.is_platform_admin:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    # Filter deleted_at IS NULL so soft-deleted members don't appear in listings
    result = await db.execute(
        select(User)
        .where(User.org_id == org_id)
        .where(User.deleted_at.is_(None))
    )
    return list(result.scalars().all())


async def change_user_role(
    db: AsyncSession, 
    org_id: uuid.UUID, 
    target_user_id: uuid.UUID, 
    new_role: UserRole, 
    current_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None
) -> User:
    enforce_role(current_user.role.value, "users", "update")
    
    if current_user.org_id != org_id and not current_user.is_platform_admin:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    result = await db.execute(select(User).where(User.id == target_user_id))
    target_user = result.scalars().first()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if target_user.org_id != org_id:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Prevent accidental self-lockout
    if target_user.id == current_user.id:
        if current_user.role in (UserRole.SUPER_ADMIN, UserRole.HR_MANAGER) and new_role not in (UserRole.SUPER_ADMIN, UserRole.HR_MANAGER):
            raise HTTPException(status_code=400, detail="Cannot demote yourself from HR Manager or Super Admin role")
            
    old_role = target_user.role
    target_user.role = new_role
    
    _create_audit_log(
        db=db,
        org_id=org_id,
        actor_id=current_user.id,
        action="role_change",
        entity_type="user",
        entity_id=target_user_id,
        diff={"before_role": old_role.value, "after_role": new_role.value},
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id
    )
    
    await db.commit()
    await db.refresh(target_user)
    
    return target_user


async def delete_org_member(
    db: AsyncSession,
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    actor_user: User,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Soft-delete a user from the organization.

    Guards (all server-side, never trusted from client):
    - actor must have org_members, delete (hr_manager only)
    - target must be in the same org and not already deleted (404 for cross-org)
    - actor cannot remove themselves via this endpoint (400)
    - cannot remove the last admin/hr_manager of the org (400)
    - revokes all active refresh tokens for the removed user (security)
    - writes audit log row
    """
    enforce_role(actor_user.role.value, "org_members", "delete")

    # The actor must belong to the org they are trying to manage
    if actor_user.org_id != org_id and not actor_user.is_platform_admin:
        raise HTTPException(status_code=404, detail="User not found")

    # Query target scoped to org + not already deleted; returns 404 for cross-org attempts
    result = await db.execute(
        select(User)
        .where(User.id == target_user_id)
        .where(User.org_id == org_id)
        .where(User.deleted_at.is_(None))
    )
    target_user = result.scalars().first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Block self-removal via this endpoint (use DELETE /users/me for self-service)
    if target_user_id == actor_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove your own account through this endpoint. Use account settings to delete your own account."
        )

    # Guard: cannot remove the last admin/hr_manager
    privileged_roles = (UserRole.SUPER_ADMIN, UserRole.HR_MANAGER)
    if target_user.role in privileged_roles:
        remaining_res = await db.execute(
            select(User)
            .where(User.org_id == org_id)
            .where(User.role.in_(privileged_roles))
            .where(User.deleted_at.is_(None))
        )
        remaining_privileged = list(remaining_res.scalars().all())
        if len(remaining_privileged) <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last admin or HR manager from the organization."
            )

    now = datetime.now(timezone.utc)
    target_user.deleted_at = now

    # Security: revoke all active refresh tokens for the removed user
    # so they cannot use existing tokens after removal.
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == target_user_id)
        .where(RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now.isoformat())
    )

    _create_audit_log(
        db=db,
        org_id=org_id,
        actor_id=actor_user.id,
        action="member_removed",
        entity_type="user",
        entity_id=target_user_id,
        diff={"removed_role": target_user.role.value},
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )

    await db.commit()


async def delete_organization(
    db: AsyncSession,
    org_id: uuid.UUID,
    actor_user: User,
    confirm_name: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    """
    Cascade soft-delete an entire organization.

    Guards:
    - actor must have is_platform_admin=True (consistent with create_organization)
    - confirm_name must exactly match org.name (server-side; prevents accidental destruction)
    - defense-in-depth: actor must belong to the org being deleted (or be platform admin)
    - all mutations happen in one transaction: org, jobs, users, interviews, applications

    Security: revokes all refresh tokens for all org users.
    """
    if not actor_user.is_platform_admin:
        raise HTTPException(status_code=403, detail="Only platform admins can delete organizations.")

    # Fetch org (must be non-deleted)
    org_res = await db.execute(
        select(Organization)
        .where(Organization.id == org_id)
        .where(Organization.deleted_at.is_(None))
    )
    org = org_res.scalars().first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Server-side confirm_name check BEFORE any mutation
    if confirm_name != org.name:
        raise HTTPException(
            status_code=400,
            detail="Name confirmation does not match the organization name. No changes were made."
        )

    now = datetime.now(timezone.utc)

    # --- All mutations in one logical transaction block ---

    # 1. Soft-delete the organization itself
    org.deleted_at = now

    # 2. Soft-delete all jobs in this org
    await db.execute(
        update(Job)
        .where(Job.org_id == org_id)
        .where(Job.deleted_at.is_(None))
        .values(deleted_at=now)
    )

    # 3. Soft-delete all users in this org
    await db.execute(
        update(User)
        .where(User.org_id == org_id)
        .where(User.deleted_at.is_(None))
        .values(deleted_at=now)
    )

    # 4. Soft-delete all interviews tied to this org's applications
    #    Interview has no direct org_id — must subquery through applications.
    from app.models.application import Application
    from app.models.interview import Interview

    org_app_ids_subq = (
        select(Application.id).where(Application.org_id == org_id)
    ).scalar_subquery()

    await db.execute(
        update(Interview)
        .where(Interview.application_id.in_(org_app_ids_subq))
        .where(Interview.deleted_at.is_(None))
        .values(deleted_at=now)
    )

    # 5. Withdraw all non-terminal applications for this org
    terminal_statuses = ("withdrawn", "rejected", "hired")
    await db.execute(
        update(Application)
        .where(Application.org_id == org_id)
        .where(Application.status.notin_(terminal_statuses))
        .values(status="withdrawn")
    )

    # Security: revoke all refresh tokens for all users in this org
    org_user_ids_subq = (
        select(User.id).where(User.org_id == org_id)
    ).scalar_subquery()

    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id.in_(org_user_ids_subq))
        .where(RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now.isoformat())
    )

    # Write audit log using the actor's org_id (may be different from org_id for platform admin)
    _create_audit_log(
        db=db,
        org_id=org_id,
        actor_id=actor_user.id,
        action="organization_deleted",
        entity_type="organization",
        entity_id=org_id,
        diff={"org_name": org.name},
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )

    await db.commit()
