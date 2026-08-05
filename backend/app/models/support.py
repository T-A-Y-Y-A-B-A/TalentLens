import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin, TenantMixin, GUID, JSONType

class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    recipient_type = Column(String, nullable=False) # user/candidate
    recipient_id = Column(GUID(), index=True, nullable=False)
    type = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    payload = Column(JSONType(), default={})
    read_at = Column(String, nullable=True)
    sent_at = Column(String, nullable=True)

class AuditLog(Base, TimestampMixin, TenantMixin):
    __tablename__ = "audit_logs"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    actor_id = Column(GUID(), index=True, nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(GUID(), index=True, nullable=False)
    diff = Column(JSONType(), default={})
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
