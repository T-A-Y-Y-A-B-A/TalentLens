from pydantic import BaseModel, EmailStr
from typing import Optional

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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class EmailVerify(BaseModel):
    token: str

class UserProfile(BaseModel):
    id: str
    email: str
    org_id: str
    role: str
    is_platform_admin: bool
    is_verified: bool
    
    class Config:
        from_attributes = True
