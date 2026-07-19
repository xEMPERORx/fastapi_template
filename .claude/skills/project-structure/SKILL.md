---
name: project-structure
description: >
  Reference for this FastAPI template's directory layout — what goes where, and when
  a flat file is enough vs. when something earns its own subfolder. Use when adding a
  new module/domain, deciding where a new utility or external-service integration
  belongs, or when a folder is starting to feel like a grab-bag of unrelated things.
---

The layout exists to answer one question fast: "if I'm adding X, which file do I open
(or create)?" Two rules drive every placement decision in this repo:

1. **Layer first, domain second.** The top-level split is always
   `routes/ → services/ → repositories/ → schema/ → models/` (see
   `fastapi-best-practices` skill for the request flow). Within a layer, group by
   domain — but only once there's more than one file's worth of reason to.
2. **A flat file until a second file shows up.** Don't create `schema/product/` for a
   single `ProductCreate`/`ProductResponse` pair — `schema/product.py` is the whole
   domain's schema layer and there's nothing to group it with yet. Promote a flat file
   to a folder the moment a domain needs a second file in that layer (see the RBAC
   example below), not before.

## Where each layer lives

| Layer | Path | Granularity |
|---|---|---|
| Routes | `app/api/v1/routes/<domain>/` or `app/api/v1/routes/<domain>.py` | Folder once a domain has >1 router file (`routes/auth/{account.py,google_oauth.py}`, `routes/rbac/{permission.py,roles.py}`). Flat otherwise (`routes/users.py`, `routes/health.py`). `main.py` imports and `include_router()`s each one. Name the main file after what it covers, not after the folder — `routes/auth/account.py`, never `routes/auth/auth.py`; a file sharing its parent folder's name reads like a typo and is always worth a more specific name (registration/login/logout/refresh/reset-password here are all "account lifecycle", hence `account.py`). |
| Services | `app/services/<domain>/` or `app/services/<domain>.py` | Folder once a domain has >1 service file. Name the file after its service class, not `service.py` (`services/rbac/{role_service.py,permission_service.py}`, `services/users/user_management_service.py`) — a generic `service.py` stops being identifiable the moment there's more than one domain folder in sight. When a domain folder itself grows past ~5-6 files covering genuinely different sub-concerns, split further: `services/auth/` keeps shared primitives (`token.py`, `password.py`, `current_user.py`) at its own top level but nests the six user-facing flows — `login.py`, `logout.py`, `register.py`, `refresh.py`, `reset_password.py`, `google_oauth.py` — under `services/auth/actions/`, since those are the "verbs" and the rest are building blocks the verbs share. |
| Repositories | `app/repositories/<domain>/<file>.py` | Same rule — `repositories/auth/{user.py,token.py}`, `repositories/rbac/{role.py,permission.py}`. |
| Schema | `app/schema/<domain>.py` or `app/schema/<domain>/` | Flat per-domain file by default (`schema/auth.py`, `schema/user.py`). Folder only when a domain's request/response models genuinely split across files worth separating (`schema/rbac/{role.py,permission.py}` — mirrors the repository/service split for the same domain). |
| Models | `app/models/<domain>.py`, exported from `app/models/db_model.py` | Always flat — one file per domain's tables. `db_model.py` is the single import surface Alembic and everything else uses. |

**Consistency across layers matters more than the folder-vs-file choice itself.** RBAC
is a folder in repositories, services, schema, *and* routes — not a folder in one and
flat files in another — because a contributor who finds `repositories/rbac/` should be
able to guess `services/rbac/`, `schema/rbac/`, and `routes/rbac/` exist too, without
checking.

## `app/core/` — grouped by concern, not dumped flat

`app/core/` is cross-cutting infrastructure, not a domain. Left flat, it silently
becomes a junk drawer as the app grows — that already happened once in this repo
(rate limiting, resilience, input validation, logging, and DI wiring all lived as
loose top-level files before being split out). The rule going forward: **a concern
gets a subpackage once it has, or will clearly grow, more than one file** — and a
package that's wired by domain (like `dependency_factory`) splits by domain the same
way any other layer does. Current subpackages:

- `core/security/` — `validation.py` (sanitization, Pydantic validators),
  `data_validation.py` (path traversal, dict/model integrity)
- `core/resilience/` — `recovery.py` (retry + `CircuitBreaker`) — add a new external
  service's breaker as a module-level instance in whatever file calls it, not a new
  file here, unless retry/circuit-breaking logic itself grows new variants
- `core/ratelimit/` — `sliding_window.py` (the Redis sorted-set algorithm),
  `limiters.py` (the shared `limiter`/`login_limiter` instances) — a new rate-limit
  algorithm (e.g. token bucket) would add a sibling module here, not replace
  `sliding_window.py`
- `core/logger/` — split by concern rather than by domain, since logging isn't
  domain-shaped: `context.py` (request-ID `ContextVar`), `formatters.py` (JSON +
  console), `setup.py` (handler construction), `emit.py` (structured log-record
  emitters + redaction), `decorators.py` (`@log_function`, `LoggedService`,
  `LoggedRepository`)
- `core/dependency_factory/` — split by domain, same as routes/services/repositories:
  `auth.py`, `rbac.py`, `users.py`, `tenant.py` — a new domain gets its own module
  here, and a factory that spans domains (like `get_user_management_service`, which
  needs both the auth and rbac repositories) lives in the domain it primarily serves
  and imports the others' factories, rather than living in some neutral fourth place.
  If that would create a circular import (e.g. `auth.py` needing a `tenant.py`
  factory, while `tenant.py` already imports from `auth.py`), define a small local
  factory in the importing module instead of forcing the import — see
  `get_tenant_repository_for_auth` in `dependency_factory/auth.py`.
- `core/rbac/` — split by concern, not domain (there's only one domain: RBAC itself):
  `delegation.py` (`effective_permissions`/`effective_permission_mask`,
  `can_grant_role`/`can_grant_permission` — the DB-backed, name/mask-based
  authorization primitives), `registry.py` (`PERMISSION_REGISTRY`, the fixed
  append-only permission catalog — bit position = index, never renumbered),
  `mask.py` (the 256-bit mask codec + `PermissionMaskType` SQLAlchemy column type),
  `principal.py` (`Principal`, the JWT-only zero-DB-query view of the caller used by
  `permission_required`'s fast path)
- `core/authz_cache/` — the in-process authorization cache kept current via Redis
  Pub/Sub with a periodic anti-entropy resync, so most requests authorize off the
  JWT alone with zero DB/network I/O: `channel.py` (Redis keys/channel constants),
  `publisher.py` (`publish_events` — called from repositories on any
  permission/role/activation mutation), `cache.py` (`AuthzCache`, the per-worker
  singleton — `is_user_inactive`/`is_tenant_inactive`/`is_stale`, all in-memory
  reads). Fails open on a Redis outage, same convention as `core/ratelimit/`.

All of the above re-export their public API from `__init__.py`, so every external
`from app.core.logger import X` / `from app.core.dependency_factory import
get_x_service` call site is unaffected by how the internals are split — only the
package's own files need to agree on where things actually live.

- **Single-file, truly one-off cross-cutting concerns stay flat at `core/` top
  level**: `dependencies.py` (RBAC route guards — `permission_required`,
  `role_required`, `grant_role_required`, `grant_permission_required`,
  `superuser_required`), `health.py`. Don't invent a subpackage for these just for
  symmetry — they don't have a second file to group with, and forcing one adds an
  import hop for no benefit.

## `app/error/` — split by domain, plus a shared base

Exceptions follow the same domain split as everything else, with one addition: a
`base.py` for the machinery every domain file builds on.

- `error/base.py` — `AppException` (the base every custom exception extends) and the
  `create_exception_handler`/`create_global_handler` factories used to register them
- `error/<domain>.py` — `auth.py`, `rbac.py`, `tenant.py`: the actual exception
  classes for that domain (`auth.py` also holds `TenantInactive`/`UserDeactivated`/
  `StaleToken` — auth-flow failures, not tenant-CRUD failures, which is why they're
  there and not in `tenant.py`)
- `error/ratelimit.py` — `RateLimit` (not domain-specific, but not generic either —
  raised by exactly one middleware)
- `error/validation.py` — `ValidationError`, `SanitizationError`
- `error/register.py` — imports every exception above and calls
  `app.add_exception_handler(...)` for each; the only file that needs to know about
  all of them at once

A new domain's exceptions go in their own `error/<domain>.py`; a new *kind* of
cross-cutting error (not tied to one domain) gets its own flat file next to
`ratelimit.py`/`validation.py`, not stuffed into `base.py`.

## `app/database/` — one file per backend, named after it

`postgres_db.py` (async engine/session — the "main" database) and `redis_db.py`
(cache/rate-limit/broker client factory). Naming them after the backend they wrap
(rather than a generic `db.py`) matters more here than folder depth: there's only one
connection per backend for the whole app, so there's nothing to further subdivide
until a second backend of the same kind shows up (e.g. a search engine, a second
Postgres replica) — at which point it gets its own `<backend>_db.py` file, same
pattern.

## Multi-tenant, bitmask-based RBAC

Beyond the hierarchical grant-delegation model, this template supports multiple
tenants sharing one deployment (`app/models/tenant.py` — shared schema, `tenant_id`
column, not schema-per-tenant): a global superuser (`tenant_id=NULL`) creates a
`Tenant` plus its first admin user in one call
(`TenantService.create_tenant_with_admin`), and from there that tenant admin creates
roles/users scoped to their own tenant without needing the superuser again.

Permissions are a **fixed, code-defined catalog** (`app.core.rbac.registry
.PERMISSION_REGISTRY`), not arbitrary DB rows — this is what makes a 256-bit
permission mask possible: every permission has a stable, append-only bit position.
`Role.permission_mask` is a cached OR-reduction of its permissions' bits, maintained
by `RoleRepository.add_permission`/`remove_permission` in the same transaction as the
underlying join-table write. A role's *creation* is bounded by a subset-mask check
(`RoleService.create_role`): a non-superuser actor may only request permissions that
are a subset of what their own roles are configured to grant
(`role_grantable_permissions`) — the same mechanism that already governed
*assigning* an existing role/permission to a user, generalized to *authoring* a new
one (`requested_mask & ~allowed_mask` is non-zero exactly when the request exceeds
what the actor may grant).

The access JWT carries the user's effective mask, tenant, and `perm_version` (see
`TokenPayload` in `app/schema/auth.py`), computed once at login/refresh
(`app.services.auth.mint.mint_access_token`) — so `permission_required` can authorize
most requests with zero DB queries via `get_current_principal` (`app/services/auth
/current_user.py`), checking only the in-process `authz_cache` for a deactivated
user/tenant or a stale mask. `role_required`/`grant_role_required`/
`grant_permission_required`/`superuser_required` stay on `get_current_user` (DB-backed,
fresh every request) since role identity and grant-delegation are open-ended and
tenant-authored, not reducible to a fixed bit position the way permissions are.

## Adding a brand-new domain (e.g. "products")

Follow the `add-feature` skill for the full step-by-step. Directory-wise, start flat
everywhere (`models/product.py`, `schema/product.py`, `repositories/product/product.py`
or `repositories/product.py`, `services/product/service.py` or `services/product.py`,
`routes/product.py`, and a `get_product_service`/`get_product_repository` pair added to
a new `core/dependency_factory/product.py`) and only fold in a folder for a given layer
once that layer needs a second file for the domain — mirroring whatever layers a
sibling domain (like RBAC) already had to split, if the new domain is conceptually
similar in shape.

## Signs a reorg is overdue

- A `core/` (or any grab-bag) file mixes two unrelated concerns because there was
  "nowhere else to put it"
- Two layers disagree on whether a domain is a folder or a flat file (breaks the
  guessability rule above)
- A domain folder has grown to hold unrelated sub-concerns that would be clearer split
  (e.g. if `services/verify/` ever needed both email-verification *and* SMS-verification
  logic with little shared code, that's a signal to split, not a signal the folder is
  wrong)
- A file's name only makes sense in isolation — `service.py`, `auth.py` nested inside
  an already-`auth`-named folder, anything you'd have to open to know what it does
  that its neighbors don't already tell you

When in doubt, match whatever the most similar existing domain already does — this
repo optimizes for "guessable from precedent" over any single abstract principle.
