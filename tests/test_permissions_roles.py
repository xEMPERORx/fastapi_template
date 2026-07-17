import pytest
from httpx import AsyncClient

from app.main import app
from tests.conftest import make_superuser, verify_user


def _iter_api_routes(routes):
    """Walk app.routes recursively.

    Since FastAPI's router-internals refactor (0.137+), `include_router()`
    no longer flattens/clones child routes into `app.routes` — it wraps each
    included router in a `_IncludedRouter` holding the original `APIRouter`
    (`.original_router`). The real `APIRoute` objects (with `.dependant`)
    live at `.original_router.routes`, potentially nested further.
    """
    for route in routes:
        if hasattr(route, "dependant"):
            yield route
        elif hasattr(route, "original_router"):
            yield from _iter_api_routes(route.original_router.routes)


@pytest.fixture(autouse=True)
def override_permission_dependencies():
    """Bypass RBAC permission guards for non-auth API tests."""
    previous = app.dependency_overrides.copy()

    async def allow_permissions():
        return None

    bypassed_names = {"permission_checker", "role_checker", "checker"}

    for route in _iter_api_routes(app.routes):
        dependant = route.dependant
        for dependency in dependant.dependencies:
            call = getattr(dependency, "call", None)
            if callable(call) and getattr(call, "__name__", "") in bypassed_names:
                app.dependency_overrides[call] = allow_permissions

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


async def register_and_login(ac: AsyncClient, username: str, email: str, password: str):
    """Scenario: Register, log in, and return (user_id, access_token)."""
    await ac.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    await verify_user(username)

    login = await ac.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    token = login.json()["access_token"]

    me = await ac.get("/api/v1/auth/user", headers={"Authorization": f"Bearer {token}"})
    return me.json()["id"], token


async def register_and_get_user_id(ac: AsyncClient, username: str, email: str, password: str):
    """Scenario: Register and get user id """
    user_id, _token = await register_and_login(ac, username, email, password)
    return user_id


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
        password="Password123!",
    )

    admin_id, admin_token = await register_and_login(
        ac,
        username="rbac-admin",
        email="rbac-admin@example.com",
        password="Password123!",
    )
    # The permission_checker/role_checker override fixture only bypasses the
    # route-level dependency; UserManagementService.assign_role re-checks
    # grant-delegation at the service layer regardless (defense in depth),
    # so the acting user still needs a real is_superuser bypass here.
    await make_superuser("rbac-admin")

    assign_response = await ac.post(
        f"/api/v1/users/{user_id}/roles/{role_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert assign_response.status_code == 204

    detail_response = await ac.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert detail_response.status_code == 200
    assert "operator" in detail_response.json()["roles"]


@pytest.mark.asyncio
async def test_role_list(ac: AsyncClient):
    """Scenario: Test role list"""
    await ac.post("/api/v1/role/", json={"name": "auditor"})
    await ac.post("/api/v1/role/", json={"name": "staff"})

    response = await ac.get("/api/v1/role/?skip=0&limit=10")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 2
