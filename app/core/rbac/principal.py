from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass(frozen=True)
class Principal:
    """The trusted, zero-DB-query view of the caller, derived entirely from
    a validated JWT plus the in-process authz cache (see
    `app.core.authz_cache`). Used by `permission_required` — checks that
    only need a permission-mask bit test, not the full `User` ORM object.

    Grant-delegation and role-name checks (`grant_role_required`,
    `grant_permission_required`, `role_required`) still need the real
    `User` with `.roles` loaded — roles are open-ended and tenant-authored,
    not a fixed bit-addressable catalog like permissions — so those stay on
    `get_current_user` (DB-backed) rather than `Principal`.
    """

    id: uuid.UUID
    tenant_id: Optional[uuid.UUID]
    is_superuser: bool
    perm_mask: int
    perm_version: int
