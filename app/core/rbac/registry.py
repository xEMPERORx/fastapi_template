"""
The fixed, append-only permission catalog.

Every permission a template deployment can ever grant is listed here, once,
with a stable bit position. This is what makes the 256-bit permission mask
(see `app.core.rbac.mask`) possible: a role's or user's effective permissions
reduce to a single integer OR-reduction instead of a set of strings, which is
what lets the mask be embedded directly in a JWT and checked with zero DB
lookups (see `app.core.authz_cache`).

Rules for editing this file:
- Only ever APPEND a new `"name": next_free_int` entry at the end.
- NEVER change an existing name's integer, and never reuse the integer of a
  removed permission — leave a `# retired, do not reuse` comment instead.
- Keep every value below 256 (a 32-byte mask). If this template ever needs
  more than 256 distinct permissions, widen `MASK_BYTES` in `mask.py` first.

`app/cli/sync_permissions.py` mirrors this registry into the `permissions`
table (`Permission.bit_position`) on every startup — it raises loudly if a
name's DB bit_position and code bit_position ever disagree, which is the
guardrail against accidentally violating the append-only rule above.
"""

PERMISSION_REGISTRY: dict[str, int] = {
    "role:create": 0,
    "role:read": 1,
    "role:read.id": 2,
    "role:update": 3,
    "role:delete": 4,
    "role:add-permission": 5,
    "role:delete-permission": 6,
    "permission:read": 7,
    "permission:read.id": 8,
    "user:read": 9,
    "user:read.id": 10,
    "user:update": 11,
    "user:deactivate": 12,
    "tenant:create": 13,
    "tenant:read": 14,
    "tenant:read.id": 15,
    "tenant:update": 16,
    "tenant:deactivate": 17,
    "user:create": 18,
    # append new entries here — never edit an existing value
}

assert len(set(PERMISSION_REGISTRY.values())) == len(PERMISSION_REGISTRY), "duplicate bit position in PERMISSION_REGISTRY"
assert max(PERMISSION_REGISTRY.values(), default=-1) < 256, "bit position exceeds 256-bit mask width"


def mask_for(names) -> int:
    """OR together the bit for each permission name. Raises `UnknownPermission`
    if any name isn't in the catalog — never silently ignored."""
    from app.error.rbac import UnknownPermission

    mask = 0
    for name in names:
        bit = PERMISSION_REGISTRY.get(name)
        if bit is None:
            raise UnknownPermission(name)
        mask |= 1 << bit
    return mask


def names_for_mask(mask: int) -> list[str]:
    """Inverse of `mask_for` — the permission names set in `mask`."""
    return [name for name, bit in PERMISSION_REGISTRY.items() if mask & (1 << bit)]


# ---------------------------------------------------------------------------
# Implied permissions — resolved once, at role-authoring time (see
# `RoleService.create_role`/`add_permission_to_role`), never at request-check
# time. This is deliberately NOT a runtime hierarchy: the mask a request
# checks against stays a flat bag of bits with a single AND per check; only
# *which bits get set* when a role is authored is affected. A write
# permission implies the read permission(s) it obviously requires, so a role
# author never has to remember to request both. Keep this list-based and
# explicit rather than inferring from name patterns (e.g. stripping a
# ":create" suffix) — implicit inference breaks silently the moment a
# permission's name doesn't fit the pattern; an explicit map fails loudly
# (KeyError-free, just "does nothing extra") and is easy to audit.
# ---------------------------------------------------------------------------
PERMISSION_IMPLIES: dict[str, tuple[str, ...]] = {
    "role:update": ("role:read", "role:read.id"),
    "role:delete": ("role:read", "role:read.id"),
    "role:add-permission": ("role:read.id",),
    "role:delete-permission": ("role:read.id",),
    "user:update": ("user:read", "user:read.id"),
    "user:deactivate": ("user:read.id",),
    "permission:read.id": ("permission:read",),
    "tenant:update": ("tenant:read.id",),
    "tenant:deactivate": ("tenant:read.id",),
}


def expand_implied(names) -> set[str]:
    """Transitively expand a requested set of permission names to include
    everything they imply. E.g. requesting only `role:update` also yields
    `role:read`/`role:read.id` in the result."""
    result = set(names)
    frontier = set(result)
    while frontier:
        next_frontier: set[str] = set()
        for name in frontier:
            for implied in PERMISSION_IMPLIES.get(name, ()):
                if implied not in result:
                    result.add(implied)
                    next_frontier.add(implied)
        frontier = next_frontier
    return result


# Permissions only ever checked via `superuser_required()` (see
# app/api/v1/routes/tenant.py's tenant CRUD) — never through
# `permission_required`, so no tenant-scoped role should actually hold them:
# a tenant admin can't create/list/update/deactivate tenants no matter what
# bits their role has, since that gate reads `actor.is_superuser` directly,
# not a mask. Excluded from `TENANT_ROLE_MASK` so the auto-created
# "tenant-admin" role doesn't carry (and display, in `GrantableSummary`)
# grants that look real but are permanently inert.
SUPERUSER_ONLY_PERMISSIONS: frozenset[str] = frozenset({
    "tenant:create",
    "tenant:read",
    "tenant:read.id",
    "tenant:update",
    "tenant:deactivate",
})

FULL_MASK: int = mask_for(PERMISSION_REGISTRY.keys())
TENANT_ROLE_MASK: int = mask_for(
    name for name in PERMISSION_REGISTRY if name not in SUPERUSER_ONLY_PERMISSIONS
)
