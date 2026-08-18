from typing import List
import uuid
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User
from app.schemas.organization import (
    OrganizationRead, OrganizationUpdate, OrganizationCreate,
    UserListItem, UserRoleUpdate, OrgDeleteConfirm
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

@router.delete("/{id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_org_member(
    id: uuid.UUID,
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft-delete a user from the organization.
    Only hr_manager can perform this action.
    Returns 404 for cross-org attempts (never 403 — prevents resource enumeration).
    Returns 400 if attempting self-removal or removing the last admin/hr_manager.
    """
    meta = _get_request_meta(request)
    await org_service.delete_org_member(
        db=db,
        org_id=id,
        target_user_id=user_id,
        actor_user=current_user,
        **meta
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    id: uuid.UUID,
    body: OrgDeleteConfirm,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cascade soft-delete an entire organization.
    Restricted to is_platform_admin users only.
    Requires confirm_name in the request body to match the org's name exactly (server-side guard).
    Soft-deletes: org, all jobs, all users, all interviews.
    Sets all non-terminal applications to 'withdrawn'.
    """
    meta = _get_request_meta(request)
    await org_service.delete_organization(
        db=db,
        org_id=id,
        actor_user=current_user,
        confirm_name=body.confirm_name,
        **meta
    )
