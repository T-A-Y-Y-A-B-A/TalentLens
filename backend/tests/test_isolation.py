import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.identity import User


@pytest.mark.asyncio
async def test_org_isolation(async_client: AsyncClient, db_session: AsyncSession):
    # ---------------------------------------------------------------
    # 1. Register User A in Org A
    # ---------------------------------------------------------------
    email_a = f"usera_{uuid.uuid4().hex[:8]}@a.com"
    org_a_name = f"Org A {uuid.uuid4().hex[:6]}"
    resp_a = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "Password123", "org_name": org_a_name}
    )
    assert resp_a.status_code == 201
    user_a = resp_a.json()

    # ---------------------------------------------------------------
    # 2. Register User B in Org B
    # ---------------------------------------------------------------
    email_b = f"userb_{uuid.uuid4().hex[:8]}@b.com"
    org_b_name = f"Org B {uuid.uuid4().hex[:6]}"
    resp_b = await async_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "Password123", "org_name": org_b_name}
    )
    assert resp_b.status_code == 201
    user_b = resp_b.json()

    # ---------------------------------------------------------------
    # 3. Verify both users via ORM
    # ---------------------------------------------------------------
    for email in [email_a, email_b]:
        result = await db_session.execute(select(User).where(User.email == email))
        db_user = result.scalars().first()
        db_user.is_verified = True
    await db_session.commit()

    # ---------------------------------------------------------------
    # 4. Login both users
    # ---------------------------------------------------------------
    login_a = await async_client.post(
        "/api/v1/auth/login", json={"email": email_a, "password": "Password123"}
    )
    assert login_a.status_code == 200
    token_a = login_a.json()["access_token"]

    login_b = await async_client.post(
        "/api/v1/auth/login", json={"email": email_b, "password": "Password123"}
    )
    assert login_b.status_code == 200
    token_b = login_b.json()["access_token"]

    # ---------------------------------------------------------------
    # 5. User A GET /me should work
    # ---------------------------------------------------------------
    me_a = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert me_a.status_code == 200

    # ---------------------------------------------------------------
    # 6. Org A user → GET /organizations/{org_b_id} → 404
    # ---------------------------------------------------------------
    org_b_id = user_b["org_id"]
    fetch_org_b = await async_client.get(
        f"/api/v1/organizations/{org_b_id}",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert fetch_org_b.status_code == 404

    # ---------------------------------------------------------------
    # 7. Org A user → GET /organizations/{org_b_id}/users → 404
    # ---------------------------------------------------------------
    fetch_org_b_users = await async_client.get(
        f"/api/v1/organizations/{org_b_id}/users",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert fetch_org_b_users.status_code == 404

    # ---------------------------------------------------------------
    # 8. Create a recruiter in Org A for RBAC tests
    # ---------------------------------------------------------------
    email_c = f"userc_{uuid.uuid4().hex[:8]}@a.com"
    resp_c = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": email_c,
            "password": "Password123",
            "org_name": f"Org C {uuid.uuid4().hex[:6]}"
        }
    )
    assert resp_c.status_code == 201
    user_c = resp_c.json()

    # Move user C into Org A with recruiter role
    res = await db_session.execute(select(User).where(User.email == email_c))
    db_user_c = res.scalars().first()
    db_user_c.is_verified = True
    db_user_c.org_id = uuid.UUID(user_a["org_id"])
    db_user_c.role = "recruiter"
    await db_session.commit()

    login_c = await async_client.post(
        "/api/v1/auth/login", json={"email": email_c, "password": "Password123"}
    )
    assert login_c.status_code == 200
    token_c = login_c.json()["access_token"]

    # ---------------------------------------------------------------
    # 9. Recruiter → PATCH /organizations/{org_a_id} → 403
    # ---------------------------------------------------------------
    org_a_id = user_a["org_id"]
    patch_org_a_recruiter = await async_client.patch(
        f"/api/v1/organizations/{org_a_id}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {token_c}"}
    )
    assert patch_org_a_recruiter.status_code == 403

    # ---------------------------------------------------------------
    # 10. Recruiter → PATCH role → 403
    # ---------------------------------------------------------------
    patch_role_recruiter = await async_client.patch(
        f"/api/v1/organizations/{org_a_id}/users/{user_c['id']}/role",
        json={"role": "hr_manager"},
        headers={"Authorization": f"Bearer {token_c}"}
    )
    assert patch_role_recruiter.status_code == 403

    # ---------------------------------------------------------------
    # 11. HR Manager → PATCH role (valid, own org) → 200 + audit log
    # ---------------------------------------------------------------
    patch_role_hr = await async_client.patch(
        f"/api/v1/organizations/{org_a_id}/users/{user_c['id']}/role",
        json={"role": "interviewer"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert patch_role_hr.status_code == 200

    # Verify audit_logs row via ORM
    from app.models.support import AuditLog
    audit_res = await db_session.execute(
        select(AuditLog).where(AuditLog.entity_id == uuid.UUID(user_c["id"]))
    )
    audit = audit_res.scalars().first()
    assert audit is not None
    assert audit.action == "role_change"

    # ---------------------------------------------------------------
    # 12. HR Manager cannot demote self
    # ---------------------------------------------------------------
    patch_own_role = await async_client.patch(
        f"/api/v1/organizations/{org_a_id}/users/{user_a['id']}/role",
        json={"role": "recruiter"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert patch_own_role.status_code == 400

    # ---------------------------------------------------------------
    # 13. Org B user → PATCH Org A user role → 404
    # ---------------------------------------------------------------
    patch_role_cross_tenant = await async_client.patch(
        f"/api/v1/organizations/{org_a_id}/users/{user_c['id']}/role",
        json={"role": "hr_manager"},
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert patch_role_cross_tenant.status_code == 404
