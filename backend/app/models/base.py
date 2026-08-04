import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr

class Base(DeclarativeBase):
    pass

class TenantMixin:
    """Mixin for tenant-owned tables to enforce org_id."""
    @declared_attr
    def org_id(cls):
        return Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

class TimestampMixin:
    """Mixin for standard timestamps."""
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
