# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your values

# Run database migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Start the application
uvicorn app.main:app --reload

# Start with specific host/port
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run specific test function
pytest tests/test_auth.py::test_register_user

# Run with coverage
pytest --cov=app

# Run with verbose output
pytest -v
```

### Docker
```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up api

# Rebuild and start
docker-compose up --build

# Stop all services
docker-compose down
```

First run: set `SEED_ADMIN_USERNAME`/`SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` in `.env` before `docker compose up` and the `api` container bootstraps that superuser automatically on startup (see `entrypoint.sh` and the `seed-admin` skill) — no manual `python -m app.cli.seed` step needed.

### Celery Worker
```bash
# Start Celery worker (for background tasks)
python -m celery -A app.queue.celery worker --loglevel=info

# Start Celery beat (for scheduled tasks)
python -m celery -A app.queue.celery beat --loglevel=info
```

## Architecture

This is a layered FastAPI backend with strict separation of concerns:

```
middleware -> route -> service -> repository -> db/external service -> response
```

### Dependency Injection Pattern

The application uses FastAPI's dependency injection system extensively. All services and repositories are wired through `app/core/dependency_factory/` — split by domain (`auth.py`, `rbac.py`, `users.py`), all re-exported from `__init__.py` so `from app.core.dependency_factory import get_x_service` is unchanged regardless of which submodule a factory actually lives in:

```python
# Repository factory
def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

# Service factory (depends on repository)
def get_login_service(
    user_repo: UserRepository = Depends(get_user_repository),
    token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> LoginUser:
    return LoginUser(user_repo, token_repo)
```

When adding new features, you must:
1. Create repository factory in `app/core/dependency_factory/<domain>.py` (new domain: add a new module)
2. Create service factory alongside it
3. Use `Annotated[ServiceType, Depends(get_service_factory)]` in routes

### Database Session Management

Database sessions are async and managed through `app/database/postgres_db.py` (named to match `redis_db.py` — both live in `app/database/`). The `get_db()` dependency provides a session that is automatically closed. In tests, this is overridden to use an in-memory SQLite database.

**Important**: Always use `await db.commit()` and `await db.refresh()` after mutations in repositories. Never commit from services or routes.

### Authentication Flow

JWT authentication uses a dual-token system:
- **Access token**: Short-lived (30 min), passed in Authorization header
- **Refresh token**: Long-lived (7 days), stored in httpOnly cookie

The flow:
1. Login creates both tokens, refresh token stored in DB and cookie
2. Access token used for authenticated requests
3. When access expires, use `/refresh` endpoint with refresh token
4. Logout revokes the refresh token in DB

The access token's claims (`TokenPayload` in `app/schema/auth.py`) carry more than identity: `tenant_id`, `is_superuser`, a hex-encoded 256-bit `perm_mask` (effective permissions), and `perm_version` — computed once at login/refresh (`app.services.auth.mint.mint_access_token`) so most requests can authorize with zero DB queries. `get_current_user` (`app/services/auth/current_user.py`) still decodes the JWT and fetches the full `User` from DB, fresh every request — use it when you need the real ORM object (e.g. `.roles`). `get_current_principal` returns a lightweight `Principal` (same file) straight from the JWT + the in-process authz cache, with no DB query at all — that's what `permission_required` uses.

### RBAC Authorization

Role-Based Access Control uses `users`, `roles`, `permissions`, with many-to-many join tables plus grant-delegation tables (`role_grantable_roles`, `role_grantable_permissions`) and a `tenants` table for multi-tenancy (`User.tenant_id`/`Role.tenant_id`, nullable — `NULL` means global).

Permissions are a **fixed, code-defined catalog** (`app.core.rbac.registry.PERMISSION_REGISTRY`) — not arbitrary DB rows created through an API — so every permission has a stable, append-only bit position and a role's/user's effective permissions reduce to a 256-bit mask (`app.core.rbac.mask`) instead of a set of strings. `app/cli/sync_permissions.py` mirrors the registry into the `permissions` table on every startup.

Authorization helpers in `app/core/dependencies.py`:
- `role_required(roles: List[str])` — checks if the user has any of the specified roles. DB-backed (`get_current_user`).
- `permission_required(required_permission: str)` — checks a single mask bit. Zero-DB-query fast path (`get_current_principal`); the permission string must already be a `PERMISSION_REGISTRY` key.
- `grant_role_required()` / `grant_permission_required()` — for endpoints that assign a role/permission to a user; data-dependent on the acting user's grant-delegation config, not a fixed string. DB-backed.
- `superuser_required()` — for operations that must never be reachable via any catalog permission (e.g. creating a tenant). DB-backed.

Usage in routes:
```python
@router.get("/admin")
async def admin_endpoint(
    current_user: User = Depends(role_required(["admin"]))
):
    ...
```

See the `project-structure` skill's "Multi-tenant, bitmask-based RBAC" section and the `fastapi-best-practices` skill's "Authentication / Authorization" section for the full mechanism (staleness detection via `app.core.authz_cache`, the role-creation subset-mask hierarchy, tenant scoping).

### Logging System

The logging system (`app/core/logger/` — split by concern into `context.py`, `formatters.py`, `setup.py`, `emit.py`, `decorators.py`, all re-exported from `__init__.py`) provides structured logging with request ID tracking across async calls:

- **Request ID**: Generated in middleware, attached to all logs via ContextVar
- **Decorators**: `@log_function` for routes, `LoggedService`/`LoggedRepository` base classes for auto-logging
- **Log types**: REQUEST_START, REQUEST_END, CALL, RESULT, ERROR
- **Output**: Beautiful console logs + JSON structured logs in `logs/` directory

When adding new services or repositories, inherit from `LoggedService` or `LoggedRepository` to get automatic logging.

### Error Handling

Exceptions are split by domain under `app/error/`:
- `base.py` — `AppException` base class + the `create_exception_handler`/`create_global_handler` factories
- `auth.py` — user/account exceptions (`UserNotFound`, `UserUnauthenticated`, `InvalidToken`, ...)
- `rbac.py` — role/permission exceptions (`RoleNotFound`, `PermissionExists`, `GrantNotAllowed`, ...)
- `ratelimit.py` — `RateLimit`
- `validation.py` — `ValidationError`, `SanitizationError`
- `register.py` — imports all of the above and registers every handler with the FastAPI app (called once from `app/main.py`)

All exceptions return JSON with `status`, `message`, and `error_code` fields.

To add a new exception:
1. Add the class to the domain file it belongs to (or create a new domain file for a new module)
2. Register its handler in `register.py` with appropriate status code
3. Raise the exception from services

### Rate Limiting

Redis-backed sliding-window-log rate limiting is implemented in `app/middleware/ratelimiting_middleware.py` using `RedisSlidingWindowLimiter` from `app/core/ratelimit/sliding_window.py` (instances in `app/core/ratelimit/limiters.py`). Default is 10 requests per 60 seconds per IP; `login_limiter` adds a stricter 5/60s per-username throttle on `/auth/login`. Correct across multiple workers/replicas since state lives in Redis, and doesn't burst at fixed-window boundaries the way a fixed-window counter does. Fails open (allows the request, logs a warning) if Redis is unreachable.

Rate limit headers are added to all responses:
- `X-RateLimit-Limit`: Max requests
- `X-RateLimit-Remaining`: Remaining requests
- `Retry-After`: Seconds until reset (when limited)

### Security Middleware

Security headers are added to every response via `app/middleware/security_middleware.py`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security` (HSTS)
- `Referrer-Policy`, `Cross-Origin-Opener-Policy`, `Permissions-Policy`

Registered automatically in `app/main.py` — no manual configuration needed.

### Input Validation

`app/core/security/validation.py` provides reusable sanitization and validation utilities:
- `sanitize_text()` — strips XSS patterns and SQL injection signatures
- `strip_html()` — HTML-encodes input
- `safe_str()` — full sanitization pipeline
- Pydantic validators: `validate_email()`, `validate_strong_password()`, `validate_no_sql_injection()`
- `SafeStr`, `SafeEmail`, `StrongPassword` — Annotated types for Pydantic schemas
- `PaginationParams` / `StrictPaginationParams` — reusable pagination models

Usage in schemas:
```python
from app.core.security.validation import SafeStr, SafeEmail, StrongPassword

class UserRegister(BaseModel):
    username: SafeStr
    email: SafeEmail
    password: StrongPassword
```

Validation exceptions are defined in `app/error/validation.py` (`ValidationError`, `SanitizationError`) and registered in `app/error/register.py`.

### Data Validation

`app/core/security/data_validation.py` provides data integrity utilities:
- `safe_filename()` — strips path traversal and dangerous characters
- `validate_model_fields()` — validates dict against Pydantic model
- `validate_required_fields()` — ensures required keys are present and non-empty
- `sanitize_dict()` — recursively truncates overly-long strings

### Error Recovery

`app/core/resilience/recovery.py` provides fault-tolerance patterns for external service calls:
- `async_retry()` — exponential backoff with jitter, configurable via `RetryConfig`
- `CircuitBreaker` — closed → open → half-open state machine, configurable via `CircuitBreakerConfig`
- `CircuitOpenError` — raised when circuit is open, mapped to 429 in error handlers

Usage:
```python
from app.core.resilience.recovery import async_retry, RetryConfig, CircuitBreaker

# Retry transient failures
result = await async_retry(external_api_call, config=RetryConfig(max_retries=3))

# Circuit breaker for fragile services
cb = CircuitBreaker("payment-service")
result = await cb.call(payment_service.charge, amount=100)
```

### Health Checks

Health check endpoints in `app/api/v1/routes/health.py`:
- `GET /api/v1/health` — aggregated status (healthy/degraded/unhealthy) with per-service details
- `GET /api/v1/health/live` — liveness probe (always 200 if app is running)
- `GET /api/v1/health/ready` — readiness probe (503 if critical services are down)

Health check logic is in `app/core/health.py` and checks database and Redis connectivity.

### Background Tasks

Celery is configured in `app/queue/celery.py` with Redis as broker. Background tasks are defined in `app/queue/task.py`.

To add a new background task:
1. Define function with `@app.task(name="task_name")` decorator
2. Call with `task_name.delay(args)` from services
3. Use `BackgroundTasks` dependency for simple async tasks that don't need Celery

### Database Models

Models are split by domain:
- `app/models/auth.py`: User, RefreshToken
- `app/models/rbac.py`: Role, Permission, user_roles, role_permissions
- `app/models/db_model.py`: Compatibility wrapper (imports from above)

When adding new models, create a new file in `app/models/` and export from `db_model.py`.

### Migrations

Alembic is configured with `migrations/env.py` importing models from `app.models.db_model`. The migration environment uses the `DB_URL` environment variable.

**Important**: After adding or modifying models, run `alembic revision --autogenerate -m "description"` to create a migration, then `alembic upgrade head` to apply it.

## Environment Configuration

All configuration is in `app/settings.py` using Pydantic Settings. Required variables are in `.env.example`.

Key environment variables:
- `DB_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`/`REFRESH_KEY`: JWT signing keys
- `MAIL_*`: SMTP configuration for email verification
- `GOOGLE_*`: OAuth credentials
- `SEED_ADMIN_USERNAME`/`SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD`: when all three are set, `entrypoint.sh` runs `python -m app.cli.seed` automatically on container startup, bootstrapping the first `is_superuser=True` account. Idempotent — a no-op once that username exists. Leave unset to skip and seed manually (see the `seed-admin` skill).

## Test Configuration

Tests use pytest-asyncio with an in-memory SQLite database. Test fixtures are in `tests/conftest.py`:
- `setup_db`: Creates/drops tables before/after each test
- `ac`: AsyncClient for making HTTP requests to the test app

Rate limiting is disabled in tests by setting `limiter.requests = 10_000`.

Test files:
- `tests/test_auth.py` — Authentication flows (register, login, logout, refresh)
- `tests/test_permissions_roles.py` — RBAC authorization
- `tests/test_validation.py` — Input sanitization and validation
- `tests/test_recovery.py` — Retry and circuit breaker
- `tests/test_data_validation.py` — Data integrity and sanitization
- `tests/test_security.py` — Security headers and health endpoints

## Claude Code Skills

This project includes Claude Code skills in `.claude/skills/` that auto-trigger to enforce conventions:

| Skill | Trigger |
|-------|---------|
| `fastapi-best-practices` | Any code under `app/` — enforces layered architecture |
| `add-feature` | "add a feature", "create a module" — full walkthrough |
| `add-endpoint` | "add an endpoint", "add a route" — endpoint quick reference |
| `write-tests` | "write tests", "test X" — test patterns and templates |
| `code-review` | "review this code" — security/architecture checklist |
| `project-structure` | Adding a new module/domain, or deciding where something goes — what goes where and when a flat file earns a folder |

Type `/skill-name` to invoke directly, or use natural language and the right skill auto-triggers.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- ALWAYS read graphify-out/GRAPH_REPORT.md before reading any source files, running grep/glob searches, or answering codebase questions. The graph is your primary map of the codebase.
- IF graphify-out/wiki/index.md EXISTS, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
