from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, UUID4

class AdminPlatformStats(BaseModel):
    total_organizations: int
    total_users: int
    total_candidates: int
    total_ai_calls: int
    active_jobs: int

class AdminOrganizationOut(BaseModel):
    id: UUID4
    name: str
    slug: str
    created_at: datetime
    users_count: int
    active_jobs_count: int

class AdminAuditLogOut(BaseModel):
    id: UUID4
    created_at: datetime
    org_name: str
    actor_email: str
    action: str
    resource_id: str
    status: str

class AdminUsageLogOut(BaseModel):
    id: UUID4
    created_at: datetime
    org_name: str
    endpoint: str
    total_tokens: float
    latency_ms: float
    candidates_matched: float
