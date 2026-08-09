from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.identity import InviteStatus

class InviteCreate(BaseModel):
    email: EmailStr
    role: str

class InviteRead(BaseModel):
    id: UUID
    email: str
    role: str
    org_id: UUID
    invited_by: UUID
    status: InviteStatus
    expires_at: str
    accepted_at: Optional[str] = None
    created_at: datetime
    
    # We will attach the shareable link on read
    link: Optional[str] = None
    
    class Config:
        from_attributes = True

class InviteAccept(BaseModel):
    token: str
    password: str
