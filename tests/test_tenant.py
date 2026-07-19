import pytest
from httpx import AsyncClient

from tests.conftest import make_superuser
from tests.test_permissions_roles import register_and_login


@pytest.mark.asyncio
async def test_superuser_can_create_tenant_with_admin(ac: AsyncClient):
    _user_id, token = await register_and_login(
        ac, username="root-super", email="root-super@example.com", password="Password123!"
    )
    await make_superuser(ac, "root-super")
    headers = {"Authorization": f"Bearer {token}"}

    response = await ac.post(
        "/api/v1/tenants/",
        json={
            "name": "acme-corp",
            "admin_username": "acme-admin",
            "admin_email": "acme-admin@example.com",
            "admin_password": "Password123!",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tenant"]["name"] == "acme-corp"
    assert body["tenant"]["is_active"] is True
    assert body["admin"]["username"] == "acme-admin"


@pytest.mark.asyncio
async def test_non_superuser_cannot_create_tenant(ac: AsyncClient):
    _user_id, token = await register_and_login(
        ac, username="not-super", email="not-super@example.com", password="Password123!"
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = await ac.post(
        "/api/v1/tenants/",
        json={
            "name": "should-fail",
            "admin_username": "should-fail-admin",
            "admin_email": "should-fail-admin@example.com",
            "admin_password": "Password123!",
        },
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "superuser_required"


@pytest.mark.asyncio
async def test_duplicate_tenant_name_rejected(ac: AsyncClient):
    _user_id, token = await register_and_login(
        ac, username="dup-super", email="dup-super@example.com", password="Password123!"
    )
    await make_superuser(ac, "dup-super")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "duplico",
        "admin_username": "duplico-admin",
        "admin_email": "duplico-admin@example.com",
        "admin_password": "Password123!",
    }
    first = await ac.post("/api/v1/tenants/", json=payload, headers=headers)
    assert first.status_code == 201

    second_payload = dict(payload, admin_username="duplico-admin2", admin_email="duplico-admin2@example.com")
    second = await ac.post("/api/v1/tenants/", json=second_payload, headers=headers)
    assert second.status_code == 400
    assert second.json()["error_code"] == "tenant_exists"


@pytest.mark.asyncio
async def test_tenant_admin_can_create_scoped_role_and_gets_full_grant(ac: AsyncClient):
    """The tenant's first admin holds a `tenant-admin` root role with every
    catalog permission and every catalog permission configured as
    grantable — enough to author further roles scoped to their own tenant
    without needing the global superuser at all."""
    _user_id, super_token = await register_and_login(
        ac, username="tenant-boot-super", email="tenant-boot-super@example.com", password="Password123!"
    )
    await make_superuser(ac, "tenant-boot-super")
    super_headers = {"Authorization": f"Bearer {super_token}"}

    create_resp = await ac.post(
        "/api/v1/tenants/",
        json={
            "name": "widgets-inc",
            "admin_username": "widgets-admin",
            "admin_email": "widgets-admin@example.com",
            "admin_password": "Password123!",
        },
        headers=super_headers,
    )
    assert create_resp.status_code == 201

    login = await ac.post(
        "/api/v1/auth/login",
        data={"username": "widgets-admin", "password": "Password123!"},
    )
    admin_token = login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    role_response = await ac.post(
        "/api/v1/role/",
        json={"name": "support-agent", "permission_names": ["user:read"]},
        headers=admin_headers,
    )

    assert role_response.status_code == 201
    assert role_response.json()["permissions"] == ["user:read"]


@pytest.mark.asyncio
async def test_deactivated_tenant_can_be_reactivated(ac: AsyncClient):
    _user_id, token = await register_and_login(
        ac, username="deact-super", email="deact-super@example.com", password="Password123!"
    )
    await make_superuser(ac, "deact-super")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await ac.post(
        "/api/v1/tenants/",
        json={
            "name": "deact-co",
            "admin_username": "deact-admin",
            "admin_email": "deact-admin@example.com",
            "admin_password": "Password123!",
        },
        headers=headers,
    )
    tenant_id = create_resp.json()["tenant"]["id"]

    deactivate = await ac.post(f"/api/v1/tenants/{tenant_id}/deactivate", headers=headers)
    assert deactivate.status_code == 204

    get_resp = await ac.get(f"/api/v1/tenants/{tenant_id}", headers=headers)
    assert get_resp.json()["is_active"] is False

    reactivate = await ac.post(f"/api/v1/tenants/{tenant_id}/activate", headers=headers)
    assert reactivate.status_code == 204

    get_resp2 = await ac.get(f"/api/v1/tenants/{tenant_id}", headers=headers)
    assert get_resp2.json()["is_active"] is True
