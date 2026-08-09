import uuid
from sqlalchemy import Column, String, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin, TenantMixin, GUID, JSONType

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    HR_MANAGER = "hr_manager"
    RECRUITER = "recruiter"
    INTERVIEWER = "interviewer"

class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    plan = Column(String, default="free")
    settings = Column(JSONType(), default={})
    
    users = relationship("User", back_populates="organization")

class User(Base, TimestampMixin, TenantMixin):
    __tablename__ = "users"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # nullable for oauth
    role = Column(Enum(UserRole), default=UserRole.HR_MANAGER, nullable=False)
    is_platform_admin = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    last_login_at = Column(String, nullable=True)
    
    organization = relationship("Organization", back_populates="users")

    @property
    def full_name(self) -> str:
        if not self.email:
            return "User"
        name_part = self.email.split("@")[0]
        formatted = " ".join(word.capitalize() for word in name_part.replace(".", " ").replace("_", " ").split())
        return formatted or self.email

class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_tokens"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), index=True, nullable=False)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(String, nullable=False)
    revoked_at = Column(String, nullable=True)

class PasswordReset(Base, TimestampMixin):
    __tablename__ = "password_resets"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), index=True, nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    expires_at = Column(String, nullable=False)
    used_at = Column(String, nullable=True)

class EmailVerification(Base, TimestampMixin):
    __tablename__ = "email_verifications"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), index=True, nullable=False)
    token_hash = Column(String, nullable=False, unique=True)
    expires_at = Column(String, nullable=False)
    used_at = Column(String, nullable=True)

class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"

class Invite(Base, TimestampMixin):
    __tablename__ = "invites"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # e.g., 'recruiter', 'interviewer'
    org_id = Column(GUID(), ForeignKey("organizations.id"), index=True, nullable=False)
    invited_by = Column(GUID(), ForeignKey("users.id"), index=True, nullable=False)
    token = Column(String, nullable=False, unique=True)
    status = Column(Enum(InviteStatus), default=InviteStatus.PENDING, nullable=False)
    expires_at = Column(String, nullable=False)
    accepted_at = Column(String, nullable=True)
