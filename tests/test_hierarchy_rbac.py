"""Tests for the hierarchical / delegated RBAC model: superuser bootstrap,
direct per-user permission grants, and role-configured grant delegation."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.db_model import User
from tests.conftest import TestingSessionLocal, verify_user


async def register_and_login(ac: AsyncClient, username: str, email: str, password: str):
    await ac.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    await verify_user(username)
    login = await ac.post("/api/v1/auth/login", data={"username": username, "password": password})
    token = login.json()["access_token"]
    me = await ac.get("/api/v1/auth/user", headers={"Authorization": f"Bearer {token}"})
    return me.json()["id"], token


async def make_superuser(username: str) -> None:
    """Simulate what the seed script does: no API path can do this — is_superuser
    is intentionally absent from every request schema."""
    async with TestingSessionLocal() as session:
        user = await session.scalar(select(User).where(User.username == username))
        user.is_superuser = True
        await session.commit()


@pytest.mark.asyncio
async def test_superuser_bypasses_permission_checks(ac: AsyncClient):
    _, token = await register_and_login(ac, "superadmin", "superadmin@example.com", "Password123!")
    await make_superuser("superadmin")

    response = await ac.post(
        "/api/v1/role/",
        json={"name": "owner"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_non_superuser_without_permission_is_forbidden(ac: AsyncClient):
    _, token = await register_and_login(ac, "plainuser", "plainuser@example.com", "Password123!")

    response = await ac.post(
        "/api/v1/role/",
        json={"name": "should-fail"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_grant_role_requires_delegation(ac: AsyncClient):
    _, admin_token = await register_and_login(ac, "rbac-admin2", "rbac-admin2@example.com", "Password123!")
    await make_superuser("rbac-admin2")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    role_resp = await ac.post("/api/v1/role/", json={"name": "team-lead"}, headers=admin_headers)
    role_id = role_resp.json()["id"]

    limited_role_resp = await ac.post("/api/v1/role/", json={"name": "limited"}, headers=admin_headers)
    limited_role_id = limited_role_resp.json()["id"]

    plain_id, plain_token = await register_and_login(ac, "plainuser2", "plainuser2@example.com", "Password123!")
    target_id, _ = await register_and_login(ac, "target-user", "target-user@example.com", "Password123!")
    plain_headers = {"Authorization": f"Bearer {plain_token}"}

    denied = await ac.post(f"/api/v1/users/{target_id}/roles/{role_id}", headers=plain_headers)
    assert denied.status_code == 403

    # Give plainuser2 the "limited" role, and configure "limited" to be able
    # to hand out "team-lead" specifically.
    await ac.post(f"/api/v1/users/{plain_id}/roles/{limited_role_id}", headers=admin_headers)
    await ac.post(f"/api/v1/role/{limited_role_id}/grantable-roles/{role_id}", headers=admin_headers)

    allowed = await ac.post(f"/api/v1/users/{target_id}/roles/{role_id}", headers=plain_headers)
    assert allowed.status_code == 204

    detail = await ac.get(f"/api/v1/users/{target_id}", headers=admin_headers)
    assert "team-lead" in detail.json()["roles"]

    # But that same "limited" role holder still can't hand out a role it
    # wasn't configured to delegate.
    other_role_resp = await ac.post("/api/v1/role/", json={"name": "finance"}, headers=admin_headers)
    other_role_id = other_role_resp.json()["id"]
    still_denied = await ac.post(f"/api/v1/users/{target_id}/roles/{other_role_id}", headers=plain_headers)
    assert still_denied.status_code == 403


@pytest.mark.asyncio
async def test_direct_permission_grant_and_revoke(ac: AsyncClient):
    _, admin_token = await register_and_login(ac, "rbac-admin3", "rbac-admin3@example.com", "Password123!")
    await make_superuser("rbac-admin3")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    perm_resp = await ac.post("/api/v1/permission/", json={"name": "reports:export"}, headers=admin_headers)
    permission_id = perm_resp.json()["id"]

    target_id, _ = await register_and_login(ac, "reportuser", "reportuser@example.com", "Password123!")

    grant_resp = await ac.post(
        f"/api/v1/users/{target_id}/permissions/{permission_id}", headers=admin_headers
    )
    assert grant_resp.status_code == 204

    detail = await ac.get(f"/api/v1/users/{target_id}", headers=admin_headers)
    assert "reports:export" in detail.json()["permissions"]
    assert "reports:export" in detail.json()["effective_permissions"]

    revoke_resp = await ac.delete(
        f"/api/v1/users/{target_id}/permissions/{permission_id}", headers=admin_headers
    )
    assert revoke_resp.status_code == 204

    detail2 = await ac.get(f"/api/v1/users/{target_id}", headers=admin_headers)
    assert "reports:export" not in detail2.json()["permissions"]


@pytest.mark.asyncio
async def test_me_grants_reflects_superuser(ac: AsyncClient):
    _, token = await register_and_login(ac, "rbac-admin4", "rbac-admin4@example.com", "Password123!")
    await make_superuser("rbac-admin4")

    resp = await ac.get("/api/v1/users/me/grants", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["is_superuser"] is True
