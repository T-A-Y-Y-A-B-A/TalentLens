import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.models.identity import User


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient, db_session: AsyncSession):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": "strongpassword123",
            "org_name": f"Test Org {uuid.uuid4().hex[:6]}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert data["role"] == "hr_manager"
    assert data["is_verified"] == False


@pytest.mark.asyncio
async def test_login_unverified(async_client: AsyncClient, db_session: AsyncSession):
    email = f"unverified_{uuid.uuid4().hex[:8]}@example.com"
    # Register first
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
            "org_name": f"Org {uuid.uuid4().hex[:6]}"
        }
    )
    assert reg.status_code == 200

    # Try logging in — should fail because not verified
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strongpassword123"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, db_session: AsyncSession):
    email = f"verified_{uuid.uuid4().hex[:8]}@example.com"

    # Register
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
            "org_name": f"Org {uuid.uuid4().hex[:6]}"
        }
    )
    assert reg.status_code == 200

    # Manually verify user in DB
    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    user.is_verified = True
    await db_session.commit()

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strongpassword123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient, db_session: AsyncSession):
    email = f"refresh_{uuid.uuid4().hex[:8]}@example.com"

    # Register + verify
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
            "org_name": f"Org {uuid.uuid4().hex[:6]}"
        }
    )
    assert reg.status_code == 200

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    user.is_verified = True
    await db_session.commit()

    # Login to get cookies
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strongpassword123"}
    )
    assert login_response.status_code == 200

    # Refresh
    refresh_response = await async_client.post("/api/v1/auth/refresh")
    print("Refresh Response:", refresh_response.text)
    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient, db_session: AsyncSession):
    email = f"logout_{uuid.uuid4().hex[:8]}@example.com"

    # Register + verify
    reg = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "strongpassword123",
            "org_name": f"Org {uuid.uuid4().hex[:6]}"
        }
    )
    assert reg.status_code == 200

    result = await db_session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    user.is_verified = True
    await db_session.commit()

    # Login
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "strongpassword123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Logout
    logout_response = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_response.status_code == 200

    # Refresh should now fail because the token is deleted/revoked
    refresh_response = await async_client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 401
