from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List, Dict, Any, Literal
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
    location: Optional[str] = Field(default=None, min_length=1, max_length=100)
    requirements: JobRequirements = Field(default_factory=JobRequirements)
    work_type: WorkType = WorkType.ONSITE
    status: JobStatus = JobStatus.DRAFT
    department_id: Optional[UUID] = None
    salary_range: Optional[str] = None
    company_description: Optional[str] = None
    key_responsibilities: Optional[List[str]] = Field(default_factory=list)
    expectations: Optional[List[str]] = Field(default_factory=list)
    benefits: Optional[List[str]] = Field(default_factory=list)

class JobCreate(JobBase):
    salary_min: int = Field(..., gt=0)
    salary_max: int = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    salary_period: Literal["yearly", "monthly"] = "yearly"

    @model_validator(mode="after")
    def check_salary_range(self):
        if self.salary_max < self.salary_min:
            raise ValueError("salary_max must be >= salary_min")
        return self

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = Field(default=None, min_length=1, max_length=100)
    requirements: Optional[JobRequirements] = None
    work_type: Optional[WorkType] = None
    status: Optional[JobStatus] = None
    department_id: Optional[UUID] = None
    salary_range: Optional[str] = None
    company_description: Optional[str] = None
    key_responsibilities: Optional[List[str]] = None
    expectations: Optional[List[str]] = None
    benefits: Optional[List[str]] = None
    
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


class JobBoardCard(BaseModel):
    id: UUID
    title: str
    org_name: str
    work_type: str
    location: str
    salary_min: int | None
    salary_max: int | None
    currency: str
    salary_period: str
    composite_score: float | None      # None if candidate has no resume yet
    flags: list[str] | None
    matched_skills: list[str] | None
    missing_skills: list[str] | None
    posted_at: datetime
    
    # JD details
    key_responsibilities: str | None = None
    expectations: str | None = None
    requirements: dict | list | str | None = None
    benefits: str | None = None
    company_description: str | None = None

class JobBoardResponse(BaseModel):
    jobs: list[JobBoardCard]
    total: int
    limit: int
    offset: int


# --- Job AI Enhancement Schemas ---

class JobEnhanceRequest(BaseModel):
    rough_notes: str

class JobEnhanceResponse(BaseModel):
    title: str
    description: str
    salary_range: Optional[str] = None
    company_description: Optional[str] = None
    key_responsibilities: Optional[List[str]] = Field(default_factory=list)
    expectations: Optional[List[str]] = Field(default_factory=list)
    benefits: Optional[List[str]] = Field(default_factory=list)
