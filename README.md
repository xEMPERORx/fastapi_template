# FastAPI Template

Production-oriented FastAPI starter built around async Python, clear service boundaries, and external infrastructure for real-world apps. Strong base for projects needing authentication, role-based access control, email verification, password reset, background jobs, database migrations, structured logging, health checks, input validation, and fault tolerance.

## What is included

- FastAPI app with versioned API routes
- Async SQLAlchemy database layer with Alembic migrations
- JWT dual-token authentication (access + refresh)
- Email verification and password reset (self-expiring signed tokens, no server-side token storage)
- Google OAuth login flow
- Hierarchical role and permission based access control (RBAC)
- Redis-backed Celery worker with background tasks
- **Structured logging** — request ID tracking, layer-aware decorators, JSON + console output
- **Input validation & sanitization** — XSS/SQL injection protection, reusable Pydantic types
- **Data validation** — path traversal prevention, model coercion, dict sanitization
- **Fault tolerance** — retry with exponential backoff + jitter, circuit breaker pattern
- **Health checks** — Kubernetes-style liveness/readiness probes with per-service status
- **Security middleware** — CSP, HSTS, X-Frame-Options, and more on every response
- **Rate limiting** — Redis-backed sliding-window limiter with standard rate-limit headers
- **Centralized error handling** — typed exceptions with JSON error responses
- Async test suite with pytest and httpx

## Tech Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x (async)
- PostgreSQL
- Redis
- Celery
- Alembic
- pytest / pytest-asyncio / httpx

## Project Structure

The codebase follows a layered architecture:

```
middleware -> route -> service -> repository -> db/external service -> response
```

- `app/main.py` — FastAPI application composition root
- `app/api/v1/routes/` — HTTP route handlers, grouped by domain: `auth/` (`account.py`, `google_oauth.py`), `rbac/` (`permission.py`, `roles.py`), plus flat `users.py`/`health.py` for single-file domains
- `app/core/` — shared utilities, grouped by concern:
  - `dependency_factory/` — DI wiring (repositories → services), split by domain: `auth.py`, `rbac.py`, `users.py`, all re-exported from `__init__.py`
  - `dependencies.py` — RBAC helpers (`role_required`, `permission_required`)
  - `rbac.py` — effective-permission computation, grant-delegation checks
  - `logger/` — structured logging with request ID, layer-aware decorators, split into `context.py`, `formatters.py`, `setup.py`, `emit.py`, `decorators.py`, re-exported from `__init__.py`
  - `health.py` — DB/Redis health checks with aggregated reporting
  - `security/` — `validation.py` (XSS/SQL injection sanitization, Pydantic validators, pagination), `data_validation.py` (path traversal prevention, model/dict validation)
  - `resilience/` — `recovery.py` (retry with backoff, circuit breaker)
  - `ratelimit/` — `sliding_window.py` (Redis sorted-set algorithm), `limiters.py` (shared `limiter`/`login_limiter` instances)
- `app/database/` — `postgres_db.py` (async engine/session) and `redis_db.py` (Redis client factory) — named to match each other
- `app/error/` — exceptions split by domain: `base.py` (base class + handler factories), `auth.py`, `rbac.py`, `ratelimit.py`, `validation.py`, plus `register.py` (registers every handler with the app)
- `app/middleware/` — request logging, rate limiting, and security headers
- `app/models/` — SQLAlchemy models, one file per domain (`auth.py`, `rbac.py`), exported through `db_model.py`
- `app/repositories/` — persistence layer, grouped by domain (`auth/`, `rbac/`)
- `app/schema/` — Pydantic request/response models, grouped by domain (`rbac/`, plus flat files for single-schema domains)
- `app/services/` — business logic, grouped by domain (`auth/` — shared primitives at the top, the six login/logout/register/refresh/reset-password/Google-OAuth flows under `auth/actions/` — `rbac/`, `users/`, `verify/`)
- `app/queue/` — Celery app and task entry points
- `migrations/` — Alembic migration scripts
- `tests/` — automated tests

See the `project-structure` Claude Code skill (`.claude/skills/project-structure/`) for the full rationale on what goes where when adding a new module.

## Available API Areas

| Area | Prefix | Description |
|------|--------|-------------|
| Authentication | `/api/v1/auth` | Register, login, logout, refresh, current user, password reset, mail verification |
| Google OAuth | `/api/v1/auth` | Authorization redirect and callback |
| Roles | `/api/v1/role` | CRUD, assign users, manage role permissions |
| Permissions | `/api/v1/permission` | CRUD, list |
| Health | `/api/v1` | Aggregated health, liveness probe, readiness probe |

Use `app/main.py` as the single place to wire new routers into the application.

## Local Setup

### 1. Create environment variables

Copy `.env.example` to `.env` and fill in real values:

```bash
cp .env.example .env
```

Key variables:

| Variable | Purpose |
|----------|---------|
| `DB_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` / `REFRESH_KEY` | JWT signing keys |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime (default 30) |
| `REFRESH_TOKEN_EXPIRE` | Refresh token lifetime in days (default 7) |
| `ALGORITHM` | JWT algorithm (HS256) |
| `MAIL_*` | SMTP settings for email verification |
| `DOMAIN` | Application domain |
| `SESSION_SECRET` | Session middleware secret |
| `CORS_ORIGINS` | Allowed CORS origins (JSON list) |
| `GOOGLE_*` | OAuth client ID, secret, redirect URI, scopes |

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run database migrations

```bash
alembic upgrade head
```

## Run Locally

### API server

```bash
uvicorn app.main:app --reload
```

The API is available at:

- `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Celery worker

```bash
python -m celery -A app.queue.celery worker --loglevel=info
```

### Celery beat (scheduled tasks)

```bash
python -m celery -A app.queue.celery beat --loglevel=info
```

## Docker Setup

The included `docker-compose.yml` starts the full stack:

- API service
- PostgreSQL
- Redis
- Celery worker

```bash
docker compose up --build
```

Service ports:

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| API | `8000` | `8000` |
| PostgreSQL | `5433` | `5432` |

The container entrypoint runs `alembic upgrade head` before starting the app.

## Testing

```bash
pytest                                    # all tests
pytest tests/test_auth.py                 # auth flows
pytest tests/test_permissions_roles.py    # RBAC
pytest tests/test_validation.py           # input sanitization
pytest tests/test_data_validation.py      # data integrity
pytest tests/test_recovery.py             # retry + circuit breaker
pytest tests/test_security.py             # security headers + health
pytest --cov=app                          # with coverage
pytest -v                                 # verbose
```

The test setup uses an isolated SQLite database, overrides the app database dependency, and relaxes the rate limiter so auth and RBAC flows can be tested reliably.

## Using the Built-in Features

### Structured Logging

All logging goes through `app/core/logger/` (split into `context.py`, `formatters.py`, `setup.py`, `emit.py`, `decorators.py` — all re-exported from the package `__init__.py`, so `from app.core.logger import ...` is unchanged regardless of which submodule something actually lives in). A unique request ID is generated per request and attached to every log line via `ContextVar`, so you can trace a request across routes, services, and repositories.

**Log output:**
- **Console** — human-readable with request/section separators
- **`logs/app_beautiful.log`** — same format, rotated at 10 MB
- **`logs/app_structured.json`** — JSON lines for log aggregation
- **`logs/errors.log`** — errors only, rotated at 10 MB

**Using decorators:**

```python
from app.core.logger import log_function, LoggedService, LoggedRepository

# On a route function
@router.get("/items")
@log_function
async def get_items(): ...

# Base classes auto-log all public methods
class MyService(LoggedService):       # layer = "service"
    async def do_work(self): ...

class MyRepo(LoggedRepository):       # layer = "repository"
    async def find_all(self): ...
```

**Direct logging:**

```python
from app.core.logger import log_info, log_warning, log_debug, log_error

log_info("User %s completed action", user_id)
log_error("PaymentError", "Charge failed", error_location="stripe.charge", exc_info=True)
```

### Input Validation & Sanitization

`app/core/security/validation.py` provides XSS and SQL injection protection you can drop into any Pydantic schema:

**Annotated types (use in schemas):**

```python
from app.core.security.validation import SafeStr, SafeEmail, StrongPassword

class UserRegister(BaseModel):
    username: SafeStr          # strips XSS + SQL injection
    email: SafeEmail           # validates format + sanitizes
    password: StrongPassword   # enforces complexity
```

**Standalone functions:**

```python
from app.core.security.validation import sanitize_text, strip_html, safe_str

sanitize_text("<script>alert(1)</script>")  # removes XSS
strip_html("<b>hello</b>")                  # HTML-encodes
safe_str(user_input)                         # full pipeline
```

**Pagination dependencies:**

```python
from app.core.security.validation import PaginationParams, StrictPaginationParams, pagination_dependency

@router.get("/items")
async def list_items(pagination: PaginationParams = Depends(pagination_dependency)):
    # pagination.page, pagination.page_size
```

### Data Validation

`app/core/security/data_validation.py` protects against path traversal and validates data integrity:

```python
from app.core.security.data_validation import safe_filename, validate_model_fields, validate_required_fields, sanitize_dict

safe_filename("../../../etc/passwd")          # → "_____etc_passwd"
validate_required_fields(data, ["name", "email"])
validated = validate_model_fields(raw_dict, MyPydanticModel)
clean = sanitize_dict(user_input)             # truncates overlong strings
```

### Fault Tolerance

`app/core/resilience/recovery.py` provides two patterns for resilient external service calls:

**Retry with exponential backoff:**

```python
from app.core.resilience.recovery import async_retry, RetryConfig

config = RetryConfig(max_retries=3, base_delay=0.5, max_delay=30.0, jitter=True)
result = await async_retry(external_api_call, arg1, arg2, config=config)
```

**Circuit breaker:**

```python
from app.core.resilience.recovery import CircuitBreaker, CircuitBreakerConfig, CircuitOpenError

cb = CircuitBreaker("payment-service", CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=30.0,
))

try:
    result = await cb.call(payment_service.charge, amount=100)
except CircuitOpenError:
    # circuit is open — fail fast, don't hammer the downstream service
```

Circuit states: **closed** (normal) → **open** (failures exceed threshold) → **half-open** (probe after timeout) → **closed** (probe succeeds).

### Health Checks

Three endpoints for orchestration and monitoring:

| Endpoint | Purpose | Behavior |
|----------|---------|----------|
| `GET /api/v1/health` | Aggregated status | Returns `healthy` / `degraded` / `unhealthy` with per-service details |
| `GET /api/v1/health/live` | Liveness probe | Always 200 if the app process is running |
| `GET /api/v1/health/ready` | Readiness probe | 200 only if DB and Redis are reachable; 503 if unhealthy |

Response format:

```json
{
  "status": "healthy",
  "checks": [
    {"service": "database", "healthy": true, "latency_ms": 2.3, "detail": "OK"},
    {"service": "redis", "healthy": true, "latency_ms": 1.1, "detail": "OK"}
  ],
  "timestamp": "2026-05-09T12:00:00Z"
}
```

To add a custom health check, add it to `run_all_checks()` in `app/core/health.py`.

### Security Middleware

Registered automatically — no manual configuration needed. Headers added to every response:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cross-Origin-Opener-Policy: same-origin`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`

### Rate Limiting

Redis-backed sliding-window-log limiter (10 requests per 60 seconds per IP by default) — accurate across multiple workers/replicas and doesn't burst at window boundaries. Instances live in `app/core/ratelimit/limiters.py`:

```python
from app.core.ratelimit.sliding_window import RedisSlidingWindowLimiter

limiter = RedisSlidingWindowLimiter(requests=10, window_seconds=60, redis_client_factory=redis_connect)
```

Headers on all responses:
- `X-RateLimit-Limit` — max requests in window
- `X-RateLimit-Remaining` — requests left
- `Retry-After` — seconds until reset (only when rate-limited)

### Error Handling

Custom exceptions all extend `AppException` (`app/error/base.py`) and return structured JSON. They're split by domain — `app/error/auth.py`, `app/error/rbac.py`, `app/error/ratelimit.py`:

```json
{
  "status": "error",
  "message": "User with this email already exists",
  "error_code": "email_exists"
}
```

Built-in exception types:
- `UsernameExist`, `UserMailExist` → 400
- `UserUnauthenticated`, `InvalidToken`, `UserNotAuthenticated` → 401
- `UserNotVerified` → 403
- `UserNotFound` → 404
- `RateLimit` → 429
- `CircuitOpenError` → 429
- `ValidationError`, `SanitizationError` → 400
- `Exception` → 500 (global catch-all)

To add a new exception:
1. Define it in the domain file it belongs to under `app/error/` (or `validation.py` for validation errors)
2. Register it in `register.py` with `create_exception_handler(status_code)`
3. Raise it from a service

### RBAC Authorization

```python
from app.core.dependencies import role_required, permission_required

@router.get("/admin")
async def admin_endpoint(
    current_user: User = Depends(role_required(["admin"]))
): ...

@router.post("/items")
async def create_item(
    current_user: User = Depends(permission_required("items:create"))
): ...
```

### Authentication Flow

Dual-token JWT system:
1. Login creates an **access token** (short-lived, in `Authorization` header) and a **refresh token** (long-lived, in httpOnly cookie)
2. Access token is used for authenticated requests
3. When access expires, call `/api/v1/auth/refresh` with the refresh cookie
4. Logout revokes the refresh token in the database

## Extending This Template

1. Add a SQLAlchemy model in `app/models/`
2. Add a repository in `app/repositories/` (inherit from `LoggedRepository`)
3. Add a service in `app/services/` (inherit from `LoggedService`)
4. Add request/response schemas in `app/schema/`
5. Add a route module in `app/api/v1/routes/`
6. Wire repository and service factories in `app/core/dependency_factory/` (add a new module for a new domain, or extend an existing one)
7. Register the router in `app/main.py`
8. Add tests under `tests/`

## Notes for Reuse

- Update CORS origins in `.env` for the frontend that will consume the API
- Keep all secrets out of version control — `.env` only
- Rotate `SECRET_KEY` and `REFRESH_KEY` for production deployments
- Review rate limit defaults before production use