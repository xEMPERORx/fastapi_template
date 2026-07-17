---
name: write-tests
description: >
  Guide for writing tests in this FastAPI template. Use when user asks to "write tests",
  "add tests", "test X", or after implementing a feature that needs test coverage.
---

Tests use pytest-asyncio with an in-memory SQLite database. Follow existing patterns in `tests/`.

## Test Setup

`tests/conftest.py` provides:
- `setup_db` fixture: creates/drops all tables before/after each test (autouse)
- `ac` fixture: `AsyncClient` pointed at the test app with dependency overrides
- Rate limiting disabled (10,000 requests per window)
- DB overridden to in-memory SQLite

## Test File Template

```python
import pytest
from httpx import AsyncClient

class TestUserRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, ac: AsyncClient):
        payload = {"username": "newuser", "email": "new@test.com", "password": "Abcdef1!"}
        response = await ac.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"

    @pytest.mark.asyncio
    async def test_register_duplicate_fails(self, ac: AsyncClient):
        payload = {"username": "dup", "email": "dup@test.com", "password": "Abcdef1!"}
        await ac.post("/api/v1/auth/register", json=payload)
        response = await ac.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_missing_field(self, ac: AsyncClient):
        payload = {"username": "test"}
        response = await ac.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, ac: AsyncClient):
        payload = {"username": "test", "email": "not-email", "password": "Abcdef1!"}
        response = await ac.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
```

## Testing Pattern by Layer

### Unit Tests (no HTTP, direct instantiation)

```python
from app.services.auth.register import RegisterUser

async def test_service_logic():
    repo = MockUserRepository()
    service = RegisterUser(repo)
    result = await service.register(user_data)
    assert result.username == "expected"
```

### Integration Tests (HTTP via AsyncClient)

```python
async def test_full_flow(ac: AsyncClient):
    # 1. Register
    r = await ac.post("/api/v1/auth/register", json={...})
    assert r.status_code == 201

    # 2. Login
    r = await ac.post("/api/v1/auth/login", data={"username": "...", "password": "..."})
    assert r.status_code == 200
    token = r.json()["access_token"]

    # 3. Authenticated request
    r = await ac.get("/api/v1/auth/user", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
```

## What to Test for Every Endpoint

| Test case | Expected |
|-----------|----------|
| Valid request | 2xx with correct response shape |
| Missing required field | 422 |
| Invalid field value | 422 or 400 |
| Unauthenticated request (auth routes) | 401 |
| Unauthorized role (admin routes) | 403 |
| Duplicate resource | 400 or 409 |
| Resource not found | 404 |
| Rate limited | 429 |

## Hierarchical RBAC Tests

`tests/test_hierarchy_rbac.py` is the reference for testing delegated-admin scenarios:
- Nothing can set `is_superuser` through the API — tests promote a user directly via a
  DB session (`TestingSessionLocal` from `tests/conftest.py`), simulating what
  `app/cli/seed.py` does, since no endpoint accepts that field.
- Test grant-delegation denial explicitly: a role with no `grantable_roles`/
  `grantable_permissions` configured must get 403 when its holder tries to assign that
  role/permission to someone, and 204 once an admin configures the delegation.
- `tests/test_permissions_roles.py`'s `override_permission_dependencies` fixture
  bypasses `permission_checker`, `role_checker`, and the `grant_role_required()`/
  `grant_permission_required()` factories' `checker` — extend the `bypassed_names` set
  there if you add a new dependency factory with its own inner function name.

Because tests run without Redis/Elasticsearch/a Celery broker, always use
`pytest --timeout=30` (via `pytest-timeout`, already a dev dependency) — a call that
forgets a connection timeout (see the `fastapi-best-practices` skill's Resilience
section) will otherwise hang the whole suite instead of failing fast.

## Core Module Unit Tests

For `app/core/` modules, write plain unit tests (no HTTP, no DB):

```python
from app.core.validation import sanitize_text, validate_email

class TestSanitizeText:
    def test_strips_xss(self):
        assert "<script>" not in sanitize_text('<script>alert(1)</script>')

    def test_strips_sql(self):
        result = sanitize_text("admin' OR 1=1 --")
        assert "1=1" not in result

class TestValidateEmail:
    def test_valid(self):
        assert validate_email("user@example.com") == "user@example.com"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            validate_email("not-an-email")
```

## Running Tests

```bash
pytest                                  # all tests
pytest tests/test_auth.py               # specific file
pytest tests/test_auth.py::TestRegister # specific class
pytest -v                               # verbose
pytest --cov=app                        # with coverage
```