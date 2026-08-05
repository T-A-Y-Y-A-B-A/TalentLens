from pydantic import BaseModel, ConfigDict, AnyHttpUrl, EmailStr, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum

class ParseStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

# ----------------- Candidate Schemas -----------------
class CandidateBase(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    source: Optional[str] = None
    profile: Optional[Dict[str, Any]] = Field(default_factory=dict)

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None

class CandidateRead(CandidateBase):
    id: UUID
    org_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

# ----------------- Resume Schemas -----------------
class ResumeBase(BaseModel):
    file_url: AnyHttpUrl

class ResumeCreate(ResumeBase):
    candidate_id: UUID

class ResumeRead(ResumeBase):
    id: UUID
    candidate_id: UUID
    parse_status: ParseStatus
    created_at: datetime
    updated_at: datetime
    
    # Converting AnyHttpUrl back to string for easier frontend consumption
    file_url: str

    model_config = ConfigDict(from_attributes=True)

class ResumeParsedDataRead(BaseModel):
    id: UUID
    resume_id: UUID
    skills: List[str]
    experience: List[Dict[str, Any]]
    education: List[Dict[str, Any]]
    certifications: List[Dict[str, Any]]
    projects: List[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)
