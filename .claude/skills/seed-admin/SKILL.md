---
name: seed-admin
description: >
  Bootstrap the first admin user on a fresh deployment of this FastAPI template.
  Use when user asks to "create the first admin", "bootstrap the app", "seed the
  database", or hits the chicken-and-egg problem where every RBAC endpoint requires
  a permission that doesn't exist yet.
---

## The problem

Every role/permission-management endpoint is gated by `permission_required(...)` or
`grant_role_required()`/`grant_permission_required()`. On a fresh database there are
no roles, no permissions, and no user has any — so nothing can create the first role
or permission through the API. `role:create`/`permission:create` gate the only way to
create roles/permissions, and nothing can grant them.

## The fix: `is_superuser`

`User.is_superuser` bypasses every permission, role, and grant-delegation check in
`app/core/dependencies.py` (see `role_required`, `permission_required`,
`grant_role_required`, `grant_permission_required`). It is deliberately **absent from
every request schema** — `UserRegister` has no `is_superuser` field, and no endpoint
accepts it — so the only way to set it is directly in the database.

## How to bootstrap

```bash
alembic upgrade head
python -m app.cli.seed
```

`app/cli/seed.py` prompts for a username/email/password (or reads
`SEED_ADMIN_USERNAME` / `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` from the
environment for non-interactive/CI bootstrap) and creates a single `is_superuser=True`
user via `UserRepository.create(..., is_superuser=True)`. No role or permission setup
is required to get started — log in as this user and they can:

1. Create roles and permissions (`POST /role/`, `POST /permission/`)
2. Attach permissions to roles (`POST /role/{id}/permissions/{permission_id}`)
3. Configure what each role is allowed to delegate to its holders
   (`POST /role/{id}/grantable-roles/{other_role_id}`,
   `POST /role/{id}/grantable-permissions/{permission_id}`)
4. Assign roles / grant direct permissions to other users
   (`POST /users/{id}/roles/{role_id}`, `POST /users/{id}/permissions/{permission_id}`)

## Rules

- Never add `is_superuser` to `UserRegister` or any other public request schema — that
  would let anyone self-promote to superuser.
- If a project needs more than one bootstrap superuser (e.g. per-environment), rerun
  the script with different env vars — it's idempotent per username
  (`UserRepository.exists_by_username` short-circuits if the user already exists).
- Prefer granting a *role* with broad permissions over minting more superusers long
  term — `is_superuser` bypasses grant-delegation entirely, so it can't be scoped or
  audited the way a role-based admin can.
