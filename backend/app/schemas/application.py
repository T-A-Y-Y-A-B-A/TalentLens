from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# ----------------- Application Schemas -----------------
class ApplicationCreate(BaseModel):
    candidate_id: UUID
    job_id: UUID

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    # We do not update stage here, we use a specific move endpoint

class ApplicationCandidate(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)

class ApplicationJob(BaseModel):
    title: str
    model_config = ConfigDict(from_attributes=True)

class ApplicationRead(BaseModel):
    id: UUID
    candidate_id: UUID
    job_id: UUID
    current_stage_id: Optional[UUID] = None
    status: str
    applied_at: str
    org_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ApplicationWithDetailsRead(ApplicationRead):
    # Eagerly loaded relations for the Candidate Portal and Frontend dropdowns
    job_title: Optional[str] = None
    stage_name: Optional[str] = None
    candidate: Optional[ApplicationCandidate] = None
    job: Optional[ApplicationJob] = None

# ----------------- Stage Movement Schemas -----------------
class ApplicationStageMove(BaseModel):
    to_stage_id: UUID
    notes: Optional[str] = None

class ApplicationStageHistoryRead(BaseModel):
    id: UUID
    application_id: UUID
    from_stage_id: Optional[UUID] = None
    to_stage_id: UUID
    moved_by: UUID
    moved_at: str
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
