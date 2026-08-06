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
    created_at: datetime
    updated_at: datetime
    
    # Optional field that gets populated if the AI parser has finished
    parsed_data: Optional['ResumeParsedDataRead'] = None

    model_config = ConfigDict(from_attributes=True)

# ----------------- Resume Schemas -----------------
class ResumeBase(BaseModel):
    file_url: str

class ResumeCreate(ResumeBase):
    candidate_id: UUID

class ResumeRead(ResumeBase):
    id: UUID
    candidate_id: UUID
    parse_status: ParseStatus
    created_at: datetime
    updated_at: datetime
    
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

# ----------------- LLM Extraction Schemas -----------------
class Experience(BaseModel):
    title: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[str] = None

class Project(BaseModel):
    name: str
    description: Optional[str] = None

class ResumeExtraction(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
