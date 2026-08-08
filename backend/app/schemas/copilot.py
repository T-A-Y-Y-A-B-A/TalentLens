from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class CopilotFilter(BaseModel):
    skills: List[str] = Field(default_factory=list, description="Specific skills mentioned by the recruiter.")
    min_experience_years: Optional[int] = Field(None, description="Minimum years of experience required.")
    certifications: List[str] = Field(default_factory=list, description="Specific certifications requested.")
    keywords: List[str] = Field(default_factory=list, description="General keywords to search for in the resume (e.g., 'machine learning', 'leadership').")
    location: Optional[str] = Field(None, description="The desired location of the candidate.")
    willingness_to_relocate: Optional[bool] = Field(None, description="Whether the candidate must be willing to relocate. Null if unspecified.")
    education_level: Optional[str] = Field(None, description="Minimum education level required (e.g., 'Bachelor', 'Master', 'PhD').")
    seniority_level: Optional[str] = Field(None, description="Seniority level expected (e.g., 'junior', 'mid', 'senior', 'lead', 'staff').")
    job_id: Optional[UUID] = Field(None, description="The UUID of the job to scope the search to. If unspecified, it searches the entire org pool.")
    exclude_stages: List[str] = Field(default_factory=list, description="Candidate pipeline stages to explicitly exclude from the search (e.g., 'rejected', 'withdrawn').")

class CopilotQueryRequest(BaseModel):
    query: str = Field(..., description="The natural language query from the recruiter.")
    job_id: Optional[UUID] = Field(None, description="Optional default job ID if the recruiter is searching from a specific job context.")

class CopilotQueryResponse(BaseModel):
    interpreted_as: CopilotFilter
    results: List[dict] = Field(..., description="List of matched candidates with their application/resume context.")
