import pytest
from httpx import AsyncClient
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Import the actual app instance and dependencies
from app.main import app
from app.core.security import get_password_hash
from app.models.identity import User, Organization, UserRole

@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient, db_session: AsyncSession):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "strongpassword123",
            "org_name": "Test Org"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "hr_manager"
    assert data["is_verified"] == False

@pytest.mark.asyncio
async def test_login_unverified(async_client: AsyncClient, db_session: AsyncSession):
    # Registration is done in the previous test or we could mock it
    # Assuming DB state persists in the test session
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )
    # Should fail because not verified
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, db_session: AsyncSession):
    # Manually verify user
    await db_session.execute(
        text("UPDATE users SET is_verified = true WHERE email = 'test@example.com'")
    )
    await db_session.commit()
    
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    
    # Check that HttpOnly cookie for refresh token is set
    assert "refresh_token" in response.cookies

@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient, db_session: AsyncSession):
    # Login first to get the cookie
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "strongpassword123"
        }
    )
    assert login_response.status_code == 200
    
    # Use the client which stores cookies automatically
    refresh_response = await async_client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in refresh_response.cookies

@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, db_session: AsyncSession):
    # Refresh to ensure we have a valid cookie session
    logout_response = await async_client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200
    
    # Refresh should now fail because the token is deleted/revoked
    refresh_response = await async_client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401
