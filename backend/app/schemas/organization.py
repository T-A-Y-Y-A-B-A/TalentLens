from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.identity import UserRole

class OrganizationRead(BaseModel):
    id: UUID
    name: str
    plan: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, extra="forbid")

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    
    model_config = ConfigDict(extra="forbid")

class OrganizationCreate(BaseModel):
    name: str
    
    model_config = ConfigDict(extra="forbid")

class UserRoleUpdate(BaseModel):
    role: UserRole
    
    model_config = ConfigDict(extra="forbid")

class UserListItem(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    role: UserRole
    is_verified: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, extra="forbid")
