from typing import List
import uuid
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User
from app.schemas.organization import (
    OrganizationRead, OrganizationUpdate, OrganizationCreate,
    UserListItem, UserRoleUpdate
)
from app.services import organization as org_service

router = APIRouter(prefix="/organizations", tags=["organizations"])

def _get_request_meta(request: Request):
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "request_id": getattr(request.state, "request_id", None)
    }

@router.post("/", response_model=OrganizationRead)
async def create_organization(
    data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.is_platform_admin:
        raise HTTPException(status_code=403, detail="Only platform admins can create organizations manually")
        
    org = await org_service.create_organization(db, data.name)
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/{id}", response_model=OrganizationRead)
async def get_organization(
    id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await org_service.get_organization(db, id, current_user)

@router.patch("/{id}", response_model=OrganizationRead)
async def update_organization(
    id: uuid.UUID,
    data: OrganizationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    meta = _get_request_meta(request)
    return await org_service.update_organization(
        db, id, data, current_user, **meta
    )

@router.get("/{id}/users", response_model=List[UserListItem])
async def list_organization_users(
    id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await org_service.list_organization_users(db, id, current_user)

@router.patch("/{id}/users/{user_id}/role", response_model=UserListItem)
async def change_user_role(
    id: uuid.UUID,
    user_id: uuid.UUID,
    data: UserRoleUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    meta = _get_request_meta(request)
    return await org_service.change_user_role(
        db, id, user_id, data.role, current_user, **meta
    )
