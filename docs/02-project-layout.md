# Project Layout — What Every File Does

Organized by layer, then by domain, matching the actual directory structure. See
[project-structure skill](../.claude/skills/project-structure/SKILL.md) for the *rules*
behind this layout (when a domain earns a folder vs. stays a flat file); this doc is
the *reference* — what's actually in each file today.

## `app/main.py`

The FastAPI app object. Registers middleware (logger → rate limit → security headers →
session → CORS), registers all exception handlers, includes every router, mounts the
admin SPA (`frontend/dist`) as a catch-all if it's been built, and defines the
`lifespan` context manager that runs `sync_permissions.sync()` and starts/stops the
`authz_cache` background tasks.

## `app/settings.py`

`Settings(BaseSettings)` — every environment variable the app needs (DB/Redis URLs,
JWT secrets/expiry, mail server, Google OAuth credentials, CORS origins), loaded from
`.env`. `Config = Settings()` is the singleton every other module imports from.

## `app/api/v1/routes/` — HTTP endpoints

| File | Endpoints |
|---|---|
| `auth/account.py` | `/register`, `/verify/{token}`, `/login`, `/logout`, `/refresh`, `/reset/password`, `/reset/password/{token}/verify`, `/user` |
| `auth/google_oauth.py` | Google OAuth authorize-redirect + callback |
| `rbac/roles.py` | Role CRUD, add/remove permission on a role, grant-delegation config (`grantable-roles`, `grantable-permissions`) |
| `rbac/permission.py` | Permission **read-only** (`GET /{id}`, `GET /`) — no create/update/delete, permissions are code-defined (see [04](./04-rbac-and-permissions.md)) |
| `tenant.py` | `POST /` (create tenant + admin), `GET /`, `GET /{id}`, `POST /{id}/deactivate`, `POST /{id}/activate` — all `superuser_required()` |
| `users.py` | List/get users, assign/remove role, grant/revoke direct permission, deactivate/activate a user, `GET /me/grants` |
| `health.py` | `/health`, `/health/live`, `/health/ready` |

## `app/schema/` — Pydantic request/response models

| File | Contents |
|---|---|
| `auth.py` | `UserRegister`, `UserLogin`, `UserResponse`, `TokenResponse`, `TokenRefreshRequest`, `TokenPayload` (the JWT claim shape — see [03](./03-authentication.md)), Google OAuth response schemas |
| `user.py` | Re-exports the auth schemas above plus `RoleSummary`, `PermissionSummary`, `UserListItem`, `UserDetail`, `GrantableSummary` |
| `rbac/role.py` | `RoleBase`/`RoleCreate` (with `permission_names: List[SafeIdentifier]`), `RoleUpdate`, `Role` (response), `RoleGrants` |
| `rbac/permission.py` | `PermissionBase`, `PermissionResponse` (no `PermissionCreate`/`Update` — see [04](./04-rbac-and-permissions.md)) |
| `tenant.py` | `TenantCreate`, `TenantResponse`, `TenantAdminResponse`, `TenantWithAdminResponse` |

## `app/models/` — SQLAlchemy tables

| File | Tables / classes |
|---|---|
| `auth.py` | `User` (incl. `tenant_id`, `perm_version`, `is_active`), `RefreshToken` |
| `rbac.py` | `Role` (incl. `tenant_id`, `permission_mask`), `Permission` (incl. `bit_position`), and five association tables: `user_roles`, `role_permissions`, `user_permissions`, `role_grantable_roles`, `role_grantable_permissions` |
| `tenant.py` | `Tenant` (`id`, `name`, `is_active`) |
| `db_model.py` | The single import surface — re-exports every model/table above; this is what `migrations/env.py` and everything else imports from |

## `app/repositories/` — the only layer that touches `db.commit()`

| File | Key methods |
|---|---|
| `auth/user.py` | `create`, `get_by_username`/`get_by_email`/`get_by_id`, `get_by_id_with_grants` (eager-loads roles→permissions and direct permissions), `list_all`/`list_by_tenant`, `grant_permission`/`revoke_permission` (bumps `perm_version`, publishes to authz cache), `set_active` (publishes `user_status` event) |
| `auth/token.py` | `RefreshTokenRepository` — create/get/revoke/delete refresh-token rows |
| `rbac/role.py` | Role CRUD, `create_root_tenant_role` (the all-permissions tenant-admin role), `add_permission`/`remove_permission` (maintains `permission_mask`, bumps every role-holder's `perm_version`), grant-delegation link management, `get_grantable_permission_mask` |
| `rbac/permission.py` | Read-only lookups (`get_by_id`, `get_by_name`, `get_by_names`, `get_by_bit_position`, `list_all`) plus `create_with_bit` (used only by `sync_permissions`) |
| `tenant/tenant.py` | `TenantRepository` — create/get/list, `set_active` (publishes `tenant_status` event) |

## `app/services/` — business logic, raises `AppException`

| File | Role |
|---|---|
| `auth/token.py` | `create_access_token`/`verify_token` (JWT encode/decode using `TokenPayload`), `create_refresh_token`/`verify_refresh_token`, the `oauth2_scheme` |
| `auth/mint.py` | `mint_access_token(user, tenant_repo)` — shared by login/refresh/Google-OAuth: checks user/tenant are active, computes the effective permission mask, calls `create_access_token` |
| `auth/current_user.py` | `get_current_user` (DB-backed, full `User`), `get_current_principal` (JWT + authz-cache only, zero DB), shared `_authenticate` helper |
| `auth/password.py` | `bcrypt` hash/verify |
| `auth/actions/register.py` | `RegisterUser.register` — duplicate checks, creates user, sends verification email via Celery |
| `auth/actions/login.py` | `LoginUser.login` — rate limit, password check, verified check, mints tokens, stores refresh token + cookie |
| `auth/actions/refresh.py` | `Refresh.refresh` — validates refresh-token row (revoked/reused/expired), rotates it, re-mints access token |
| `auth/actions/logout.py` | `LogoutUser.logout` — deletes the refresh-token row, clears the cookie |
| `auth/actions/reset_password.py` | `ResetPassword` — sends the reset-link email (fire-and-forget background task) |
| `auth/actions/google_oauth.py` | `GoogleOAuthService` — OAuth redirect + callback, find-or-create user, mint tokens |
| `rbac/role_service.py` | Role CRUD with tenant-scope guard (`_ensure_role_in_scope`), `create_role`'s subset-mask hierarchy check, grant-delegation configuration |
| `rbac/permission_service.py` | Read-only (`get_permission`, `get_all_permissions`) |
| `tenant/tenant_service.py` | `create_tenant_with_admin`, `get_tenant`, `list_tenants`, `set_tenant_active` |
| `users/user_management_service.py` | List/get users, `assign_role`/`remove_role`/`grant_permission`/`revoke_permission` (delegation-checked via `can_grant_role`/`can_grant_permission`), `set_user_active`, `get_grants` |
| `verify/mail_config.py` | `fastapi-mail` connection config + `create_message` |
| `verify/mail_verify.py` | `VerifyMail.verify_mail` — decodes the emailed token, marks the user verified |
| `verify/password_reset.py` | `PasswordReset.verify_password` — decodes the reset token, sets the new password |
| `verify/utils.py` | `itsdangerous` serializers: `create_url_safe_token`/`decode_url_safe_token` (24h, email verification), `create_password_reset_token`/`decode_password_reset_token` (30 min, separate salt) |

## `app/core/` — cross-cutting infrastructure (grouped by concern, not domain)

| Package/file | Purpose |
|---|---|
| `dependencies.py` | The five route guards: `role_required`, `permission_required`, `grant_role_required`, `grant_permission_required`, `superuser_required` |
| `dependency_factory/{auth,rbac,users,tenant}.py` | Every repository/service factory, split by domain, re-exported from `__init__.py` |
| `rbac/registry.py` | `PERMISSION_REGISTRY` — the fixed, append-only permission catalog (name → bit position) |
| `rbac/mask.py` | `PermissionMaskType` (SQLAlchemy column type) + mask↔bytes↔hex codec functions |
| `rbac/principal.py` | `Principal` — the JWT-only, zero-DB-query view of the caller |
| `rbac/delegation.py` | `effective_permissions`/`effective_permission_mask` (DB-backed), `can_grant_role`/`can_grant_permission` |
| `authz_cache/channel.py` | Redis key/channel name constants |
| `authz_cache/publisher.py` | `publish_events` — writes the durable Redis mirror + publishes to Pub/Sub |
| `authz_cache/cache.py` | `AuthzCache` — the per-worker in-memory cache, Pub/Sub subscriber, anti-entropy resync loop |
| `ratelimit/sliding_window.py` | `RedisSlidingWindowLimiter` — the sorted-set sliding-window algorithm |
| `ratelimit/limiters.py` | The shared `limiter` (per-IP) and `login_limiter` (per-username) instances |
| `resilience/recovery.py` | `async_retry`/`retry` (exponential backoff + jitter), `CircuitBreaker`/`CircuitBreakerConfig` |
| `security/validation.py` | `sanitize_text`, `strip_html`, `safe_str`, Pydantic validators (`validate_email`, `validate_strong_password`, `validate_no_sql_injection`), `SafeStr`/`SafeEmail`/`StrongPassword`/`SafeIdentifier` annotated types, pagination params |
| `security/data_validation.py` | `safe_filename`, `validate_model_fields`, `validate_required_fields`, `sanitize_dict` |
| `logger/{context,formatters,setup,emit,decorators}.py` | Request-ID `ContextVar`, JSON/console formatters, handler setup, structured log emitters + secret redaction, `@log_function`/`LoggedService`/`LoggedRepository` |
| `health.py` | `HealthStatus`/`HealthReport`, `check_db`/`check_redis`/`run_all_checks` |

## `app/error/` — exceptions, split by domain

| File | Contents |
|---|---|
| `base.py` | `AppException`, `create_exception_handler`/`create_global_handler` factories |
| `auth.py` | `UserException` + `UsernameExist`, `UserMailExist`, `UserUnauthenticated`, `UserNotVerified`, `InvalidToken`, `UserNotAuthenticated`, `UserNotFound`, `UserDeactivated`, `TenantInactive`, `StaleToken` |
| `rbac.py` | `RBACException` + role/permission/grant exceptions, `UnknownPermission`, `SuperuserRequired` |
| `tenant.py` | `TenantException`, `TenantNotFound`, `TenantExists` |
| `ratelimit.py` | `RateLimit` |
| `validation.py` | `ValidationError`, `SanitizationError` |
| `register.py` | Imports every exception above, registers a handler for each via `app.add_exception_handler` |

## `app/database/` — connection factories

| File | Purpose |
|---|---|
| `postgres_db.py` | `Base`, `engine` (async SQLAlchemy engine), `get_db()` dependency |
| `redis_db.py` | `redis_connect()` — a fresh, short-timeout `redis.asyncio.Redis` client per call |

## `app/middleware/`

| File | Purpose |
|---|---|
| `logger_middleware.py` | Assigns a request ID, logs start/end + duration, attaches `X-Request-ID` header |
| `ratelimiting_middleware.py` | Per-IP sliding-window check on every request, adds `X-RateLimit-*` headers |
| `security_middleware.py` | Adds the fixed set of security headers to every response |

## `app/queue/` — Celery

| File | Purpose |
|---|---|
| `celery.py` | Celery app config — Redis broker/backend, `task_ignore_result=True`, connect timeouts, the beat schedule (nightly `cleanup_expired_tokens`) |
| `task.py` | `send_email_bg` (fire-and-forget email sending), `cleanup_expired_tokens` (deletes expired/revoked refresh-token rows) |

## `app/cli/`

| File | Purpose |
|---|---|
| `seed.py` | One-time bootstrap: creates the first `is_superuser=True` user (the only way to set that flag) |
| `sync_permissions.py` | Mirrors `PERMISSION_REGISTRY` into the `permissions` table — idempotent, run on every app startup via `lifespan` |

## `migrations/`

| File | What it adds |
|---|---|
| `10328bfc2473_create_initial_tables.py` | `users`, `roles`, `permissions`, `role_permissions`, `user_roles`, `refreshtoken` |
| `2d86ed6bd641_hierarchical_rbac.py` | `is_superuser`, `created_by_id`, `user_permissions`, `role_grantable_roles`, `role_grantable_permissions` |
| `4ad43bc4d43b_permission_bit_position.py` | `permissions.bit_position` |
| `4a36f94508d1_tenants.py` | `tenants` table, `users.tenant_id`/`is_active`/`perm_version`, `roles.tenant_id`/`permission_mask`, the two role-name uniqueness constraints |
| `env.py` | Alembic environment — imports `Base`/models from `app.models.db_model`, reads `DB_URL` from settings |
