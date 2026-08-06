from pydantic import BaseModel, EmailStr, field_serializer
from typing import Optional
from uuid import UUID

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    org_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class OauthRegisterRequest(BaseModel):
    reg_token: str
    org_name: str

class OauthPreviewResponse(BaseModel):
    email: str
    name: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class EmailVerify(BaseModel):
    token: str

class UserProfile(BaseModel):
    id: UUID
    email: str
    org_id: UUID
    role: str
    is_platform_admin: bool
    is_verified: bool

    model_config = {"from_attributes": True}

    @field_serializer("id", "org_id")
    def serialize_uuid(self, v: UUID) -> str:
        return str(v)
