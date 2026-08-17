from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.recruitment import JobStatus, WorkType

# --- Department Schemas ---

class DepartmentBase(BaseModel):
    name: str

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    
    model_config = ConfigDict(extra="forbid")

class DepartmentRead(DepartmentBase):
    id: UUID
    org_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# --- Pipeline Stage Schemas ---

class PipelineStageBase(BaseModel):
    name: str
    order_index: int

class PipelineStageCreate(PipelineStageBase):
    pass

class PipelineStageUpdate(BaseModel):
    name: Optional[str] = None
    order_index: Optional[int] = None
    
    model_config = ConfigDict(extra="forbid")

class PipelineStageRead(PipelineStageBase):
    id: UUID
    job_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Job Schemas ---

class JobRequirements(BaseModel):
    required_skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = None
    education: Optional[str] = None

class JobBase(BaseModel):
    title: str
    description: str
    requirements: JobRequirements = Field(default_factory=JobRequirements)
    work_type: WorkType
    status: JobStatus = JobStatus.DRAFT
    department_id: Optional[UUID] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[JobRequirements] = None
    work_type: Optional[WorkType] = None
    status: Optional[JobStatus] = None
    department_id: Optional[UUID] = None
    
    model_config = ConfigDict(extra="forbid")

class JobRead(JobBase):
    id: UUID
    org_id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    pipeline_stages: List[PipelineStageRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

class JobPublicRead(JobBase):
    id: UUID
    org_id: UUID
    created_at: datetime
    department: Optional[DepartmentRead] = None
    
    model_config = ConfigDict(from_attributes=True)
