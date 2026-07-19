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

All services and repositories wired through `app/core/dependency_factory/`, split by domain (`auth.py`, `rbac.py`, `users.py`, `tenant.py`, all re-exported from `__init__.py` — import from `app.core.dependency_factory` either way). Follow this pattern:

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
6. Wire dependencies in `app/core/dependency_factory/` (new module for a new domain)
7. Register router in `app/main.py`
8. Run `alembic revision --autogenerate -m "description"`

### New Route Only
1. Schema in `app/schema/`
2. Route function in `app/api/v1/routes/`
3. Dependencies in `app/core/dependency_factory/`
4. Router in `app/main.py`

## Database Rules

- Always use async SQLAlchemy: `AsyncSession`, `select()`, `await db.commit()`
- Commit + refresh after mutations in repository, never in service or route
- Use `selectinload` for relationships: `select(Model).options(selectinload(Model.related))`
- Never commit from services or routes — only repositories touch the session

## Error Handling

- Raise exceptions from the domain file they belong to under `app/error/` (`auth.py`, `rbac.py`, ...), never return error dicts
- Custom exceptions extend `AppException` (`app/error/base.py`) and take `(message, error_code)`
- Register new exception handlers in `app/error/register.py`
- Use `create_exception_handler(status_code, initial_detail)` factory
- Service layer validates and raises, route layer never handles errors

## Logging

- Routes: use `@log_function` decorator
- Services: extend `LoggedService` for auto-logging of all public methods
- Repositories: extend `LoggedRepository` for auto-logging
- Sensitive fields (password, token, secret, key) auto-redacted

## Authentication / Authorization

- `get_current_user` dep for endpoints that need the real `User` object (returns it with `.roles`, `.permissions`, `.is_superuser` eagerly loaded — see `UserRepository.get_by_id_with_grants`). DB-backed, fresh every request.
- `get_current_principal` dep returns a `Principal` (`app/core/rbac/principal.py`) — `id`/`tenant_id`/`is_superuser`/`perm_mask`/`perm_version` decoded straight from the JWT, zero DB query. Used internally by `permission_required`; reach for it directly only if a route needs those fields without the full `User`.
- `role_required(["admin"])` for role-based access — DB-backed (`get_current_user`), since roles are open-ended/tenant-authored and can't be reduced to a fixed bit position.
- `permission_required("resource:action")` for fine-grained control — mask-based, zero-DB-query fast path via `get_current_principal`. The permission string must already be a key in `app.core.rbac.registry.PERMISSION_REGISTRY` (checked at route-decoration/import time, not per-request) — permissions are a fixed, code-defined catalog, not arbitrary runtime strings.
- `grant_role_required()` / `grant_permission_required()` for endpoints that assign a role/permission to a user (path params `role_id`/`permission_id`) — the allowed set is per-actor and data-dependent, not a fixed string; DB-backed, see `app/core/rbac/delegation.py`.
- `superuser_required()` for operations that must never be reachable via any catalog permission (e.g. creating a tenant) — checks `User.is_superuser` directly, DB-backed, no permission string can substitute for it.
- `User.is_superuser` bypasses every one of the above checks — it exists purely to bootstrap the first admin (see `app/cli/seed.py`) and is never settable through any request schema. It's also baked into the access token as its own claim (`TokenPayload.is_superuser`) since a mask-only proxy can't express it for grant-delegation/role-name checks.
- Access tokens in Authorization header, refresh tokens in httpOnly cookie **and** returned in the login/refresh JSON body (the frontend keeps both in memory to drive its own refresh calls, since `/auth/refresh` reads the token from the request body, not the cookie)
- **Any privilege change (role assignment, permission grant/revoke, superuser promotion) doesn't retroactively update an already-issued access token.** The token remains valid until it naturally expires, but `permission_required`'s fast path will see a stale `perm_version` (401 `stale_token`) once the mutation publishes to the authz cache — the client is expected to call `/auth/refresh` (or re-login) to pick up the change, not treat this as an error to work around.

## Hierarchical RBAC (delegated administration) + multi-tenancy

Beyond flat role/permission checks, roles carry their own delegation config:

- `Role.grantable_roles` / `Role.grantable_permissions` (via `role_grantable_roles` / `role_grantable_permissions` tables): which roles/permissions a *holder* of this role may hand out to other users. Configured with `RoleService.add_grantable_role` / `add_grantable_permission` and the `/role/{id}/grantable-roles/...` and `/role/{id}/grantable-permissions/...` endpoints.
- The same `role_grantable_permissions` table also bounds what a non-superuser may put in a **new** role at creation time (`RoleService.create_role`'s subset-mask check: `requested_mask & ~allowed_mask`) — holding a permission and being allowed to grant it are two separate things; a role needs both to usefully author further roles (see the `project-structure` skill's "Multi-tenant, bitmask-based RBAC" section for the full mechanism).
- `user_permissions` table: direct per-user permission grants that bypass roles entirely — for a permission that needs to reach exactly one person without inventing a role for it. Managed through `UserManagementService` / `POST|DELETE /users/{id}/permissions/{permission_id}`.
- `GET /users/me/grants` returns the caller's effective permissions plus what they're personally allowed to grant — frontends use it to only offer choices that won't 403, but the backend re-checks on every mutating call regardless.
- `Tenant` (`app/models/tenant.py`): a global superuser creates a tenant plus its first admin user in one call (`POST /api/v1/tenants/`, superuser-only). `User.tenant_id`/`Role.tenant_id` are nullable — `NULL` means global (a superuser, or a system role available to every tenant). `RoleService`'s scope guard (`_ensure_role_in_scope`) stops a non-superuser from mutating a role outside their own tenant, raising `RoleNotFound` rather than a 403 to avoid confirming another tenant's role even exists.
- A deactivated user or tenant (`User.is_active`/`Tenant.is_active`, toggled via `POST /users/{id}/deactivate` or `POST /api/v1/tenants/{id}/deactivate`) is blocked immediately at the authz-cache layer (`app.core.authz_cache`), not just at natural token expiry.

## Input Validation

- Use Pydantic models for all request bodies
- Use `Annotated[str, AfterValidator(...)]` from `app/core.validation` for field-level checks
- Available validators (in `app/core/security/validation.py`): `validate_email`, `validate_strong_password`, `validate_no_sql_injection`, `sanitize_text`, `sanitize_identifier` (for slugs/usernames derived from other input, e.g. OAuth email prefixes)
- Available types: `SafeStr`, `SafeEmail`, `StrongPassword`, `SafeIdentifier` — `SafeStr` is for free-text fields (it strips SQL keywords, so never use it on scoped names). `SafeIdentifier` is a strict allow-list (`[a-zA-Z0-9_.:-]`) for structured identifiers like `RoleBase`/`PermissionBase` names — permission naming convention is `resource:action` (`role:create`, `permission:delete`), and those verbs are exactly the SQL keywords `SafeStr`/`sanitize_text` strips, so it silently mangles them (`"permission:create"` → `"permission:"`). Reject-don't-mangle is the rule for anything an authorization check will later match against verbatim.

## Error Recovery

- Use `async_retry(func, config=RetryConfig(max_retries=3))` for transient external calls
- Use a **module-level** `CircuitBreaker` instance for external services that may fail repeatedly — never instantiate one per-call, it needs to persist failure state across requests. Create one per external service you integrate (e.g. `payment_breaker = CircuitBreaker("payment-gateway")`) — there are currently none in the template since nothing yet calls out to a service that needs one.
- Import from `app.core.resilience.recovery`

## Security

- All responses get security headers automatically (registered via middleware)
- Health check at `/api/v1/health` for monitoring (database + Redis connectivity)
- Rate limiting is a Redis-backed sliding-window log (`app.core.ratelimit.limiters`, algorithm in `app.core.ratelimit.sliding_window`) so limits hold across multiple workers/replicas, not just one process, and don't burst at fixed-window boundaries. It fails open (allows the request, logs a warning) if Redis itself is unreachable rather than taking the API down. `login_limiter` adds a stricter per-username throttle on `/auth/login` independent of the general per-IP limiter.
- Password-reset tokens are self-expiring signed tokens (`itsdangerous.URLSafeTimedSerializer`, see `app/services/verify/utils.py`'s `create_password_reset_token`/`decode_password_reset_token`, 30 min max age) — no Redis storage/lookup needed, the expiry is encoded in the token itself. Email-verification tokens use the same library with a longer-lived (24h) separate serializer/salt.
- Never log secrets — logger auto-redacts password/token/key fields
- Any code path that calls out to Redis/Celery must set an explicit connect timeout — the sync `redis` client Celery's result backend uses has no default timeout and can block a request thread for a very long time if the broker is down. Fire-and-forget tasks should also set `task_ignore_result=True`; without it, `.delay()` sets up a result-tracking subscription even when nothing ever calls `.get()`.
- The authz cache (`app.core.authz_cache`) follows the same fail-open convention as the rate limiter: if Redis/Pub-Sub is unreachable, a worker keeps serving from whatever it last knew (or "nothing known revoked" on a cold start), logging loudly, rather than blocking every authenticated request. An outage degrades authorization freshness, not availability — a deliberate tradeoff, not an oversight; if a deployment needs the opposite (fail closed), that's a change to `AuthzCache`/`get_current_principal`, not something to route around per-endpoint.

## Frontend

The admin SPA in `frontend/` (Vite + React + TypeScript + shadcn/ui) is served from this same FastAPI process via `app.frontend("/", directory="frontend/dist")` in `app/main.py` (requires `fastapi>=0.138.0`) — no separate frontend server. API routes always win; the SPA is only served as a fallback when no `@app.get(...)` matched. The mount is skipped automatically if `frontend/dist` doesn't exist yet, so pure-backend dev never breaks — run `npm run build` in `frontend/` first. See the `add-admin-page` skill for frontend conventions.

## What NOT To Do

- Don't put business logic in route functions
- Don't call `db.commit()` outside repositories
- Don't return raw SQLAlchemy models from routes — use response schemas
- Don't catch exceptions in routes — let the global handler deal with them
- Don't create circular imports — dependency_factory isolates all wiring
- Don't skip layers to save time — the pattern exists for a reason