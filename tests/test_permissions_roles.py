import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture(autouse=True)
def override_permission_dependencies():
    """Bypass RBAC permission guards for non-auth API tests."""
    previous = app.dependency_overrides.copy()

    async def allow_permissions():
        return None

    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if not dependant:
            continue
        for dependency in dependant.dependencies:
            call = getattr(dependency, "call", None)
            if callable(call) and getattr(call, "__name__", "") == "permission_checker":
                app.dependency_overrides[call] = allow_permissions

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


async def register_and_get_user_id(ac: AsyncClient, username: str, email: str, password: str):
    """Scenario: Register and get user id """
    await ac.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )

    login = await ac.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    token = login.json()["access_token"]

    me = await ac.get("/api/v1/auth/user", headers={"Authorization": f"Bearer {token}"})
    return me.json()["id"]


@pytest.mark.asyncio
async def test_permission_create_and_get(ac: AsyncClient):
    """Scenario: create and get permission """
    create_response = await ac.post(
        "/api/v1/permission/",
        json={"name": "permission:create"},
    )

    assert create_response.status_code == 201
    permission_id = create_response.json()["id"]

    get_response = await ac.get(f"/api/v1/permission/{permission_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "permission:create"


@pytest.mark.asyncio
async def test_permission_list(ac: AsyncClient):
    """Scenario: Test permission list"""
    await ac.post("/api/v1/permission/", json={"name": "permission:read"})
    await ac.post("/api/v1/permission/", json={"name": "permission:update"})

    response = await ac.get("/api/v1/permission/?skip=0&limit=10")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_role_create_and_get(ac: AsyncClient):
    """Scenario: Role create and get role """
    create_response = await ac.post(
        "/api/v1/role/",
        json={"name": "manager"},
    )

    assert create_response.status_code == 201
    role_id = create_response.json()["id"]

    get_response = await ac.get(f"/api/v1/role/{role_id}")

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "manager"


@pytest.mark.asyncio
async def test_assign_role_to_user(ac: AsyncClient):
    """Scenario: assign role to the user """
    role_response = await ac.post("/api/v1/role/", json={"name": "operator"})
    role_id = role_response.json()["id"]

    user_id = await register_and_get_user_id(
        ac,
        username="rbac-user",
        email="rbac@example.com",
        password="password123",
    )

    assign_response = await ac.get(f"/api/v1/role/{user_id}/assign/{role_id}")

    assert assign_response.status_code == 200


@pytest.mark.asyncio
async def test_role_list(ac: AsyncClient):
    """Scenario: Test role list"""
    await ac.post("/api/v1/role/", json={"name": "auditor"})
    await ac.post("/api/v1/role/", json={"name": "staff"})

    response = await ac.get("/api/v1/role/?skip=0&limit=10")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2
