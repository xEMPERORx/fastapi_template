---
name: fastapi-best-practices
description: >
  Enforce FastAPI best practices and project conventions. Auto-triggers when writing
  FastAPI code, routes, services, repositories, middleware, or modifying any file under app/.
  Use when user asks to "follow best practices", "make it production-ready", or writes
  any FastAPI endpoint/service/repository.
---

Always follow this project's layered architecture and conventions. Never bypass layers.

## Architecture

```
middleware -> route -> service -> repository -> db/external service -> response
```

Every request flows through these layers. Never skip a layer. Never put business logic in routes. Never put DB queries in services.

## Dependency Injection

All services and repositories wired through `app/core/dependency_factory.py`. Follow this pattern:

```python
# Repository factory
def get_thing_repository(db: AsyncSession = Depends(get_db)) -> ThingRepository:
    return ThingRepository(db)

# Service factory
def get_thing_service(
    thing_repo: ThingRepository = Depends(get_thing_repository),
) -> ThingService:
    return ThingService(thing_repo)
```

Routes use `Annotated[ServiceType, Depends(get_service_factory)]`.

## When Adding Code

### New Feature (full stack)
1. Pydantic schemas in `app/schema/` (request + response models)
2. SQLAlchemy model in `app/models/` (export from `db_model.py`)
3. Repository in `app/repositories/` (extend `LoggedRepository`)
4. Service in `app/services/` (extend `LoggedService`)
5. Route in `app/api/v1/routes/`
6. Wire dependencies in `app/core/dependency_factory.py`
7. Register router in `app/main.py`
8. Run `alembic revision --autogenerate -m "description"`

### New Route Only
1. Schema in `app/schema/`
2. Route function in `app/api/v1/routes/`
3. Dependencies in `app/core/dependency_factory.py`
4. Router in `app/main.py`

## Database Rules

- Always use async SQLAlchemy: `AsyncSession`, `select()`, `await db.commit()`
- Commit + refresh after mutations in repository, never in service or route
- Use `selectinload` for relationships: `select(Model).options(selectinload(Model.related))`
- Never commit from services or routes — only repositories touch the session

## Error Handling

- Raise exceptions from `app/error/custom_exception.py`, never return error dicts
- Custom exceptions extend `AppException` and take `(message, error_code)`
- Register new exception handlers in `app/error/register_error.py`
- Use `create_exception_handler(status_code, initial_detail)` factory
- Service layer validates and raises, route layer never handles errors

## Logging

- Routes: use `@log_function` decorator
- Services: extend `LoggedService` for auto-logging of all public methods
- Repositories: extend `LoggedRepository` for auto-logging
- Sensitive fields (password, token, secret, key) auto-redacted

## Authentication / Authorization

- `get_current_user` dep for authenticated endpoints (returns a `User` with `.roles`, `.permissions`, `.is_superuser` eagerly loaded — see `UserRepository.get_by_id_with_grants`)
- `role_required(["admin"])` for role-based access
- `permission_required("write:users")` for fine-grained control — checks the union of role-derived and direct-granted permissions via `app.core.rbac.effective_permissions`
- `grant_role_required()` / `grant_permission_required()` for endpoints that assign a role/permission to a user (path params `role_id`/`permission_id`) — the allowed set is per-actor and data-dependent, not a fixed string; see `app/core/rbac.py`
- `User.is_superuser` bypasses every one of the above checks — it exists purely to bootstrap the first admin (see `app/cli/seed.py`) and is never settable through any request schema
- Access tokens in Authorization header, refresh tokens in httpOnly cookie **and** returned in the login/refresh JSON body (the frontend keeps both in memory to drive its own refresh calls, since `/auth/refresh` reads the token from the request body, not the cookie)

## Hierarchical RBAC (delegated administration)

Beyond flat role/permission checks, roles carry their own delegation config:

- `Role.grantable_roles` / `Role.grantable_permissions` (via `role_grantable_roles` / `role_grantable_permissions` tables): which roles/permissions a *holder* of this role may hand out to other users. Configured with `RoleService.add_grantable_role` / `add_grantable_permission` and the `/role/{id}/grantable-roles/...` and `/role/{id}/grantable-permissions/...` endpoints.
- `user_permissions` table: direct per-user permission grants that bypass roles entirely — for a permission that needs to reach exactly one person without inventing a role for it. Managed through `UserManagementService` / `POST|DELETE /users/{id}/permissions/{permission_id}`.
- `GET /users/me/grants` returns the caller's effective permissions plus what they're personally allowed to grant — frontends use it to only offer choices that won't 403, but the backend re-checks on every mutating call regardless.

## Input Validation

- Use Pydantic models for all request bodies
- Use `Annotated[str, AfterValidator(...)]` from `app/core.validation` for field-level checks
- Available validators: `validate_email`, `validate_strong_password`, `validate_no_sql_injection`, `sanitize_text`, `sanitize_identifier` (for slugs/usernames derived from other input, e.g. OAuth email prefixes)
- Available types: `SafeStr`, `SafeEmail`, `StrongPassword`, `SafeIdentifier` — `SafeStr` is for free-text fields (it strips SQL keywords, so never use it on scoped names). `SafeIdentifier` is a strict allow-list (`[a-zA-Z0-9_.:-]`) for structured identifiers like `RoleBase`/`PermissionBase` names — permission naming convention is `resource:action` (`role:create`, `permission:delete`), and those verbs are exactly the SQL keywords `SafeStr`/`sanitize_text` strips, so it silently mangles them (`"permission:create"` → `"permission:"`). Reject-don't-mangle is the rule for anything an authorization check will later match against verbatim. Free-text query params (e.g. search) should be run through `sanitize_text` in the service before reaching an external query (Elasticsearch, etc.) — mangling is an acceptable/expected outcome there since it's not matched verbatim afterward.

## Error Recovery

- Use `async_retry(func, config=RetryConfig(max_retries=3))` for transient external calls
- Use a **module-level** `CircuitBreaker` instance for external services that may fail repeatedly — never instantiate one per-call, it needs to persist failure state across requests. Shared instances live in `app.core.circuit_breakers` (`es_breaker`, `redis_breaker`) and already wrap `SearchRepository.search` and the Redis calls in password reset.
- Import from `app.core.recovery`

## Security

- All responses get security headers automatically (registered via middleware)
- Health check at `/api/v1/health` for monitoring
- Rate limiting is Redis-backed (`app.core.rate_limiters`) so limits hold across multiple workers/replicas, not just one process. It fails open (allows the request, logs a warning) if Redis itself is unreachable rather than taking the API down. `login_limiter` adds a stricter per-username throttle on `/auth/login` independent of the general per-IP limiter.
- Never log secrets — logger auto-redacts password/token/key fields
- Any code path that calls out to Redis/Celery must set an explicit connect timeout — the sync `redis` client Celery's result backend uses has no default timeout and can block a request thread for a very long time if the broker is down. Fire-and-forget tasks should also set `task_ignore_result=True`; without it, `.delay()` sets up a result-tracking subscription even when nothing ever calls `.get()`.

## Frontend

The admin SPA in `frontend/` (Vite + React + TypeScript + shadcn/ui) is served from this same FastAPI process via `app.frontend("/", directory="frontend/dist")` in `app/main.py` (requires `fastapi>=0.138.0`) — no separate frontend server. API routes always win; the SPA is only served as a fallback when no `@app.get(...)` matched. The mount is skipped automatically if `frontend/dist` doesn't exist yet, so pure-backend dev never breaks — run `npm run build` in `frontend/` first. See the `add-admin-page` skill for frontend conventions.

## What NOT To Do

- Don't put business logic in route functions
- Don't call `db.commit()` outside repositories
- Don't return raw SQLAlchemy models from routes — use response schemas
- Don't catch exceptions in routes — let the global handler deal with them
- Don't create circular imports — dependency_factory isolates all wiring
- Don't skip layers to save time — the pattern exists for a reason