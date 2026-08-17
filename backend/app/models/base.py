import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, TypeDecorator, types
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr
import json


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's UUID type when available, otherwise stores as a
    CHAR(36) string. This lets the same models work against both
    PostgreSQL (production) and SQLite (tests).
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class JSONType(TypeDecorator):
    """Platform-independent JSON type.

    Uses PostgreSQL's JSONB when available, otherwise falls back to
    a TEXT column with manual JSON serialisation (for SQLite).
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB
            return dialect.type_descriptor(JSONB)
        return dialect.type_descriptor(String)

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if hasattr(value, "model_dump"):  # Pydantic BaseModel
            value = value.model_dump(mode="json")
        if dialect.name == "postgresql":
            return value  # psycopg2 handles dict → JSONB natively
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, dict) or isinstance(value, list):
            return value
        return json.loads(value)


class Base(DeclarativeBase):
    pass

class TenantMixin:
    """Mixin for tenant-owned tables to enforce org_id."""
    @declared_attr
    def org_id(cls):
        return Column(GUID(), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False, index=True)

class TimestampMixin:
    """Mixin for standard timestamps."""
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
