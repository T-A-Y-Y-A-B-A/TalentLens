import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.identity import User, UserRole
from app.core.security import enforce_role

async def change_user_role(db: AsyncSession, current_user: User, target_user_id: str, new_role: UserRole) -> Optional[User]:
    """
    Change a user's role. Enforces RBAC at the service layer so this cannot be bypassed.
    """
    # Enforce at the service layer using Casbin
    enforce_role(current_user.role.value, "users", "update_role")
    
    result = await db.execute(select(User).where(User.id == target_user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.org_id != current_user.org_id and not current_user.is_platform_admin:
        raise HTTPException(status_code=403, detail="Cannot modify users outside your organization")
        
    user.role = new_role
    await db.commit()
    await db.refresh(user)
    
    return user
