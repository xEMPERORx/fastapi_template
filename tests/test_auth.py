import uuid
import pytest
from httpx import AsyncClient
from app.main import app
from app.services.auth.current_user import get_current_user
from tests.conftest import verify_user
import os
os.environ["ENV"] = "testing"

MOCK_USER_ID = str(uuid.uuid4())

class MockUser:
    id = MOCK_USER_ID
    email = "test@example.com"
    username = "testuser"

async def mock_get_current_user():
    return MockUser()


@pytest.mark.asyncio
async def test_register_user(ac: AsyncClient):
    """Test: Registering User """
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Password123!"
    }
    response = await ac.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_register_invalid_data(ac: AsyncClient):
    """Test: Sending an invalid email and a short password"""
    payload = {
        "email": "not-an-email",
        "username": "testuser2",
        "password": "1"
    }
    response = await ac.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_user(ac: AsyncClient):
    """Test POST /api/v1/auth/login using Form Data"""
    login_data = {
        "username": "testuser",
        "password": "Password123!"
    }
    payload = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "Password123!"
    }
    response = await ac.post("/api/v1/auth/register", json=payload)
    await verify_user("testuser")
    response = await ac.post("/api/v1/auth/login", data=login_data)

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()



@pytest.mark.asyncio
async def test_get_current_user_info(ac: AsyncClient):
    """Test GET /api/v1/auth/user with Dependency Injection"""
    app.dependency_overrides[get_current_user] = mock_get_current_user

    response = await ac.get("/api/v1/auth/user")

    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_get_user_unauthenticated(ac: AsyncClient):
    """Scenario: User provides NO token at all"""
    app.dependency_overrides.pop(get_current_user, None)

    response = await ac.get("/api/v1/auth/user")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_get_user_invalid_token(ac: AsyncClient):
    """Scenario: User provides a 'junk' token"""
    headers = {"Authorization": "Bearer this-is-not-a-real-token"}
    response = await ac.get("/api/v1/auth/user", headers=headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(ac: AsyncClient):
    """Test: Login with correct username but incorrect password"""
    reg_payload = {
        "email": "wrongpass@example.com",
        "username": "wrongpasstest",
        "password": "CorrectPassword123!"
    }
    await ac.post("/api/v1/auth/register", json=reg_payload)

    login_data = {
        "username": "wrongpasstest",
        "password": "this_is_incorrect"
    }
    response = await ac.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
