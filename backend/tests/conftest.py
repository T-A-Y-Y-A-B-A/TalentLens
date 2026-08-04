import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
import os

# Ensure we use test DB or handle safely
from app.main import app
from app.core.database import get_db
from app.core.database import engine, AsyncSessionLocal

@pytest_asyncio.fixture(scope="session")
async def db_session():
    # Provide a session for tests
    async with AsyncSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(scope="session")
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
