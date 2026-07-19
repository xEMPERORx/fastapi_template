import pytest
from httpx import AsyncClient

from tests.conftest import make_superuser
from tests.test_permissions_roles import register_and_login


async def _permission_id_by_name(ac: AsyncClient, headers: dict, name: str) -> int:
    """`permission_required` isn't bypassed in this test file (that override
    fixture lives in `test_permissions_roles.py`, scoped to that module
    only), so this needs a real, authenticated superuser token."""
    response = await ac.get("/api/v1/permission/?skip=0&limit=200", headers=headers)
    for perm in response.json():
        if perm["name"] == name:
            return perm["id"]
    raise AssertionError(f"permission '{name}' not found in catalog — sync_permissions may not have run")


@pytest.mark.asyncio
async def test_superuser_can_create_role_with_any_catalog_permissions(ac: AsyncClient):
    """Scenario: superuser bypasses the subset-mask check entirely."""
    _user_id, _token = await register_and_login(
        ac, username="super-creator", email="super-creator@example.com", password="Password123!"
    )
    token = await make_superuser(ac, "super-creator")
    headers = {"Authorization": f"Bearer {token}"}

    response = await ac.post(
        "/api/v1/role/",
        json={"name": "super-role", "permission_names": ["role:create", "user:read"]},
        headers=headers,
    )

    assert response.status_code == 201
    assert set(response.json()["permissions"]) == {"role:create", "user:read"}


@pytest.mark.asyncio
async def test_role_creation_within_grantable_permissions_succeeds(ac: AsyncClient):
    """Scenario: 'admin can create another admin' — an actor whose role is
    configured to grant 'user:read' may author a new role requesting exactly
    that permission (a subset of what they're allowed to grant)."""
    admin_id, _admin_token = await register_and_login(
        ac, username="hierarchy-admin", email="hierarchy-admin@example.com", password="Password123!"
    )
    admin_token = await make_superuser(ac, "hierarchy-admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # The grantor role needs "role:create" as one of its OWN permissions
    # (the coarse `permission_required("role:create")` route gate every
    # caller must clear) in addition to "user:read" configured as
    # grantable (the fine subset-mask hierarchy check inside
    # `RoleService.create_role`) — these are deliberately two separate
    # things: holding a permission vs. being allowed to hand it to others.
    grantor_role = await ac.post(
        "/api/v1/role/",
        json={"name": "grantor", "permission_names": ["role:create"]},
        headers=admin_headers,
    )
    grantor_role_id = grantor_role.json()["id"]

    user_read_id = await _permission_id_by_name(ac, admin_headers, "user:read")
    grant_response = await ac.post(
        f"/api/v1/role/{grantor_role_id}/grantable-permissions/{user_read_id}",
        headers=admin_headers,
    )
    assert grant_response.status_code == 204

    actor_id, _actor_token = await register_and_login(
        ac, username="tenant-admin-actor", email="tenant-admin-actor@example.com", password="Password123!"
    )
    assign_response = await ac.post(
        f"/api/v1/users/{actor_id}/roles/{grantor_role_id}",
        headers=admin_headers,
    )
    assert assign_response.status_code == 204

    # The actor's earlier token was minted before this role assignment, so
    # its `perm_mask`/`perm_version` claims are now stale (the assignment
    # bumped `perm_version` and published it — see
    # `RoleRepository.assign_to_user`) — a fresh login is required to pick
    # up the new permissions, same as a real client would need to do.
    relogin = await ac.post(
        "/api/v1/auth/login", data={"username": "tenant-admin-actor", "password": "Password123!"}
    )
    actor_token = relogin.json()["access_token"]

    actor_headers = {"Authorization": f"Bearer {actor_token}"}
    create_response = await ac.post(
        "/api/v1/role/",
        json={"name": "support-agent", "permission_names": ["user:read"]},
        headers=actor_headers,
    )

    assert create_response.status_code == 201
    assert create_response.json()["permissions"] == ["user:read"]


@pytest.mark.asyncio
async def test_role_creation_exceeding_grantable_permissions_denied(ac: AsyncClient):
    """Scenario: 'staff cannot create an admin' — an actor whose role is only
    configured to grant 'user:read' may NOT author a role requesting
    'role:create', since that exceeds what they're allowed to grant."""
    admin_id, _admin_token = await register_and_login(
        ac, username="hierarchy-admin2", email="hierarchy-admin2@example.com", password="Password123!"
    )
    admin_token = await make_superuser(ac, "hierarchy-admin2")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    grantor_role = await ac.post(
        "/api/v1/role/",
        json={"name": "limited-grantor", "permission_names": ["role:create"]},
        headers=admin_headers,
    )
    grantor_role_id = grantor_role.json()["id"]

    user_read_id = await _permission_id_by_name(ac, admin_headers, "user:read")
    await ac.post(
        f"/api/v1/role/{grantor_role_id}/grantable-permissions/{user_read_id}",
        headers=admin_headers,
    )

    actor_id, _actor_token = await register_and_login(
        ac, username="staff-actor", email="staff-actor@example.com", password="Password123!"
    )
    await ac.post(
        f"/api/v1/users/{actor_id}/roles/{grantor_role_id}",
        headers=admin_headers,
    )

    # As above: the role assignment bumped this user's `perm_version`, so
    # their earlier token is now stale — re-login to pick up "role:create"
    # before attempting (and failing) the over-broad role creation.
    relogin = await ac.post(
        "/api/v1/auth/login", data={"username": "staff-actor", "password": "Password123!"}
    )
    actor_token = relogin.json()["access_token"]

    actor_headers = {"Authorization": f"Bearer {actor_token}"}
    create_response = await ac.post(
        "/api/v1/role/",
        json={"name": "wanna-be-admin", "permission_names": ["role:create"]},
        headers=actor_headers,
    )

    assert create_response.status_code == 403
    assert create_response.json()["error_code"] == "grant_not_allowed"


@pytest.mark.asyncio
async def test_role_creation_with_unknown_permission_name_rejected(ac: AsyncClient):
    """Scenario: a permission name outside the fixed catalog is rejected
    rather than silently accepted or auto-created."""
    _user_id, _token = await register_and_login(
        ac, username="unknown-perm-actor", email="unknown-perm-actor@example.com", password="Password123!"
    )
    token = await make_superuser(ac, "unknown-perm-actor")
    headers = {"Authorization": f"Bearer {token}"}

    response = await ac.post(
        "/api/v1/role/",
        json={"name": "bogus-role", "permission_names": ["not:a-real-permission"]},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "unknown_permission"
