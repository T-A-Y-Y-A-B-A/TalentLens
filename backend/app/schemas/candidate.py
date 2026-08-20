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
    
    # The active resume for this candidate
    resume: Optional['ResumeRead'] = None

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
    certifications: List[str]
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

    @property
    def experience_bullets(self) -> List[str]:
        return [exp.description for exp in self.experience if exp.description]

    @property
    def experience_titles(self) -> List[str]:
        return [exp.title for exp in self.experience if exp.title]

    @property
    def total_years_experience(self) -> Optional[float]:
        years = 0.0
        has_dates = False
        from datetime import datetime
        import re
        for exp in self.experience:
            if not exp.start_date or not exp.end_date:
                continue
            
            def extract_year(date_str: str) -> Optional[int]:
                if date_str.lower() in ("present", "current", "now"):
                    return datetime.utcnow().year
                match = re.search(r'\b(19|20)\d{2}\b', date_str)
                if match:
                    return int(match.group(0))
                return None
                
            start_yr = extract_year(exp.start_date)
            end_yr = extract_year(exp.end_date)
            
            if start_yr and end_yr and end_yr >= start_yr:
                years += (end_yr - start_yr)
                has_dates = True
        return years if has_dates else None
