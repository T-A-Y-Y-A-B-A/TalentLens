from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.identity import User
from app.schemas.recruitment import DepartmentCreate, DepartmentUpdate, DepartmentRead
from app.services.recruitment import (
    get_departments, create_department, update_department, delete_department
)

router = APIRouter(prefix="/departments", tags=["departments"])

@router.get("", response_model=List[DepartmentRead])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_departments(db, current_user)

@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_new_department(
    department: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await create_department(db, department, current_user)

@router.patch("/{department_id}", response_model=DepartmentRead)
async def update_existing_department(
    department_id: UUID,
    department: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await update_department(db, department_id, department, current_user)

@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_department(
    department_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await delete_department(db, department_id, current_user)
