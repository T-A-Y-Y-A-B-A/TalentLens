from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.models.candidate import Candidate
from app.models.identity import User
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.core.security import enforce_role
from app.core.exceptions import DomainException

async def create_candidate(db: AsyncSession, obj_in: CandidateCreate, current_user: User) -> Candidate:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    # Optional: check if candidate already exists in org? We'll allow duplicates for now unless unique by email per org
    
    db_obj = Candidate(
        org_id=current_user.org_id,
        email=obj_in.email,
        name=obj_in.name,
        phone=obj_in.phone,
        source=obj_in.source,
        profile=obj_in.profile,
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

async def get_candidates(db: AsyncSession, current_user: User) -> List[Candidate]:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    result = await db.execute(
        select(Candidate)
        .where(Candidate.org_id == current_user.org_id)
        # Note: no deleted_at on candidates in current schema, if there was, we'd filter it
    )
    return result.scalars().all()

async def get_candidate(db: AsyncSession, candidate_id: UUID, current_user: User) -> Candidate:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    result = await db.execute(
        select(Candidate)
        .where(Candidate.id == candidate_id)
        .where(Candidate.org_id == current_user.org_id)
    )
    db_obj = result.scalars().first()
    if not db_obj:
        raise DomainException("candidate_not_found", "Candidate not found", status_code=404)
        
    return db_obj

async def update_candidate(db: AsyncSession, candidate_id: UUID, obj_in: CandidateUpdate, current_user: User) -> Candidate:
    enforce_role(current_user.role.value, "candidates", "manage")
    
    db_obj = await get_candidate(db, candidate_id, current_user)
    
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    await db.commit()
    await db.refresh(db_obj)
    return db_obj
