"""
Test configuration: file-based SQLite database + mocked Redis.

Each test gets its own engine/session created within the test's event loop,
avoiding the cross-event-loop issues with pytest-asyncio's function-scoped loops.
"""
import os
import tempfile

# --- Environment overrides MUST come before any app imports ---
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-jwt-signing-only"
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-google-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-google-client-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://localhost/callback")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("MINIO_ACCESS_KEY", "test")
os.environ.setdefault("MINIO_SECRET_KEY", "test")

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ---------------------------------------------------------------------------
# 1. Mock Redis BEFORE importing any app module that touches it
# ---------------------------------------------------------------------------
_redis_state = {}

async def _mock_redis_get(key, *args, **kwargs):
    return _redis_state.get(key)

async def _mock_redis_setex(key, time, value, *args, **kwargs):
    _redis_state[key] = value
    return True

def _mock_sync_redis_setex(key, time, value, *args, **kwargs):
    _redis_state[key] = value
    return True

_mock_redis = AsyncMock()
_mock_redis.get = AsyncMock(side_effect=_mock_redis_get)
_mock_redis.setex = AsyncMock(side_effect=_mock_redis_setex)
_mock_redis.delete = AsyncMock(return_value=True)
_mock_redis.aclose = AsyncMock(return_value=None)

import app.core.security as security_module
security_module.redis_client = _mock_redis

import redis
import redis.asyncio

def _mock_async_from_url(*args, **kwargs):
    return _mock_redis

_mock_sync_redis = MagicMock()
_mock_sync_redis.setex = MagicMock(side_effect=_mock_sync_redis_setex)

def _mock_sync_from_url(*args, **kwargs):
    return _mock_sync_redis

redis.asyncio.Redis.from_url = _mock_async_from_url
redis.Redis.from_url = _mock_sync_from_url

# Mock celery tasks to prevent hanging trying to connect to Redis broker
import app.services.email as email_service
email_service.send_verification_email = MagicMock()
email_service.send_password_reset_email = MagicMock()

import sys
mock_matching = MagicMock()
mock_matching.match_candidates_task = MagicMock()
mock_matching.match_candidates_task.delay = MagicMock()
sys.modules["app.workers.tasks.matching"] = mock_matching

# ---------------------------------------------------------------------------
# 2. Import the FastAPI app and models
# ---------------------------------------------------------------------------
from app.main import app as fastapi_app
from app.core.database import get_db
from app.models.base import Base
import app.models  # noqa: F401 – register all models with Base.metadata

# ---------------------------------------------------------------------------
# 3. Determine a temp file for the SQLite database (persists across tests in
#    the same session, cleaned up by the OS later).
# ---------------------------------------------------------------------------
_db_fd, _db_path = tempfile.mkstemp(suffix=".db", prefix="talentlens_test_")
os.close(_db_fd)  # close the fd; SQLAlchemy will open it itself
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_db_path}"


# ---------------------------------------------------------------------------
# 4. Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def db_session():
    """Create a fresh engine + tables + session inside the test's event loop."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture()
async def async_client():
    """
    HTTPX AsyncClient wired to the FastAPI app.
    The app's get_db dependency is overridden to use the test SQLite DB.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    # Disable rate limits during testing
    fastapi_app.state.limiter.enabled = False

    fastapi_app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        yield client

    fastapi_app.dependency_overrides.clear()
    await engine.dispose()
