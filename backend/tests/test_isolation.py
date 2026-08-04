import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import uuid

@pytest.mark.asyncio
async def test_org_isolation(async_client: AsyncClient, db_session: AsyncSession):
    # Register User A in Org A
    org_a_name = f"Org A {uuid.uuid4()}"
    resp_a = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"usera_{uuid.uuid4()}@a.com",
            "password": "Password123",
            "org_name": org_a_name
        }
    )
    assert resp_a.status_code == 200
    user_a = resp_a.json()
    
    # Register User B in Org B
    org_b_name = f"Org B {uuid.uuid4()}"
    resp_b = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"userb_{uuid.uuid4()}@b.com",
            "password": "Password123",
            "org_name": org_b_name
        }
    )
    assert resp_b.status_code == 200
    user_b = resp_b.json()
    
    # Manually verify them
    await db_session.execute(text(f"UPDATE users SET is_verified = true WHERE email IN ('{user_a['email']}', '{user_b['email']}')"))
    await db_session.commit()
    
    # Login as User A
    login_a = await async_client.post("/api/v1/auth/login", json={"email": user_a['email'], "password": "Password123"})
    token_a = login_a.json()["access_token"]
    
    # Login as User B
    login_b = await async_client.post("/api/v1/auth/login", json={"email": user_b['email'], "password": "Password123"})
    token_b = login_b.json()["access_token"]
    
    # User A fetching themselves via /me should work
    me_a = await async_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_a.status_code == 200
    
    # Org A user -> GET /organizations/{org_b_id} -> assert 404
    org_b_id = user_b["org_id"]
    fetch_org_b = await async_client.get(f"/api/v1/organizations/{org_b_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert fetch_org_b.status_code == 404
    
    # Org A user -> GET /organizations/{org_b_id}/users -> assert 404
    fetch_org_b_users = await async_client.get(f"/api/v1/organizations/{org_b_id}/users", headers={"Authorization": f"Bearer {token_a}"})
    assert fetch_org_b_users.status_code == 404

    # Create Recruiter in Org A (so we have a non-HR_MANAGER role to test with)
    # We will just change user A's role manually in DB, or create a new user C
    resp_c = await async_client.post(
        "/api/v1/auth/register",
        json={"email": f"userc_{uuid.uuid4()}@a.com", "password": "Password123", "org_name": f"Org C {uuid.uuid4()}"}
    )
    user_c = resp_c.json()
    from sqlalchemy import select
    from app.models.identity import User
    
    res = await db_session.execute(select(User).where(User.email == user_c['email']))
    db_user_c = res.scalar_one()
    db_user_c.is_verified = True
    db_user_c.org_id = user_a['org_id']
    db_user_c.role = "recruiter"
    await db_session.commit()
    
    login_c = await async_client.post("/api/v1/auth/login", json={"email": user_c['email'], "password": "Password123"})
    token_c = login_c.json()["access_token"]
    
    # Org A recruiter -> PATCH /organizations/{org_a_id} -> assert 403
    org_a_id = user_a["org_id"]
    patch_org_a_recruiter = await async_client.patch(f"/api/v1/organizations/{org_a_id}", json={"name": "New Name"}, headers={"Authorization": f"Bearer {token_c}"})
    assert patch_org_a_recruiter.status_code == 403
    
    # Org A recruiter -> PATCH /organizations/{org_a_id}/users/{user_id}/role -> assert 403
    patch_role_recruiter = await async_client.patch(f"/api/v1/organizations/{org_a_id}/users/{user_c['id']}/role", json={"role": "hr_manager"}, headers={"Authorization": f"Bearer {token_c}"})
    assert patch_role_recruiter.status_code == 403
    
    # Org A hr_manager -> PATCH /organizations/{org_a_id}/users/{user_id}/role (own org, valid target) -> assert 200, assert audit_logs row
    patch_role_hr = await async_client.patch(f"/api/v1/organizations/{org_a_id}/users/{user_c['id']}/role", json={"role": "interviewer"}, headers={"Authorization": f"Bearer {token_a}"})
    assert patch_role_hr.status_code == 200
    
    # Verify audit_logs row
    audit_res = await db_session.execute(text(f"SELECT action FROM audit_logs WHERE entity_id = '{user_c['id']}'"))
    audit_action = audit_res.scalar()
    assert audit_action == "role_change"
    
    # hr_manager attempts to change own role away from hr_manager -> assert rejected
    patch_own_role = await async_client.patch(f"/api/v1/organizations/{org_a_id}/users/{user_a['id']}/role", json={"role": "recruiter"}, headers={"Authorization": f"Bearer {token_a}"})
    assert patch_own_role.status_code == 400
