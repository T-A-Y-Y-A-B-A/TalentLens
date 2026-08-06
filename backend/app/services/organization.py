import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.identity import User, Organization, UserRole
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
        
    result = await db.execute(select(User).where(User.org_id == org_id))
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
