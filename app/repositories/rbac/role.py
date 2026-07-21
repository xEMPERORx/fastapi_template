import uuid

from sqlalchemy import delete, exists, insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.authz_cache import publish_events
from app.core.logger import LoggedRepository
from app.models.db_model import (
    Permission,
    Role,
    User,
    role_grantable_permissions,
    role_grantable_roles,
    user_roles,
)
from app.schema.rbac.role import RoleCreate


class RoleRepository(LoggedRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: int) -> Role | None:
        return await self.db.scalar(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )

    async def get_by_name(self, name: str, tenant_id: uuid.UUID | None = None) -> Role | None:
        return await self.db.scalar(
            select(Role).where(Role.name == name, Role.tenant_id == tenant_id)
        )

    async def get_by_ids(self, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []
        result = await self.db.scalars(
            select(Role).options(selectinload(Role.permissions)).where(Role.id.in_(role_ids))
        )
        return result.unique().all()

    async def create(
        self,
        role: RoleCreate,
        tenant_id: uuid.UUID | None = None,
        permissions: list[Permission] | None = None,
        permission_mask: int = 0,
    ) -> Role:
        db_role = Role(name=role.name, tenant_id=tenant_id, permission_mask=permission_mask)
        if permissions:
            db_role.permissions = permissions
        self.db.add(db_role)
        await self.db.commit()
        await self.db.refresh(db_role)
        return await self.get_by_id(db_role.id)

    async def create_root_tenant_role(self, tenant_id: uuid.UUID, allowed_permission_mask: int) -> Role:
        """The first role for a brand-new tenant's admin user — sets
        `permission_mask` to `allowed_permission_mask` (the tenant's
        superuser-configured ceiling, see `TenantService.create_tenant_with_admin`
        and `Tenant.allowed_permission_mask`), clamped to `TENANT_ROLE_MASK`
        as a hard backstop, and configures it as able to grant all of those
        to others.

        Deliberately excludes `SUPERUSER_ONLY_PERMISSIONS` (`tenant:*`) —
        those are only ever checked via `superuser_required()`, never a mask
        bit, so granting them here would be a real permission bit that does
        nothing except confusingly show up as "held" in the tenant admin's
        grants."""
        from app.core.rbac.registry import SUPERUSER_ONLY_PERMISSIONS, TENANT_ROLE_MASK

        effective_mask = allowed_permission_mask & TENANT_ROLE_MASK
        all_rows = (
            await self.db.scalars(
                select(Permission).where(Permission.name.notin_(SUPERUSER_ONLY_PERMISSIONS))
            )
        ).all()
        permission_rows = [
            p for p in all_rows if p.bit_position is not None and effective_mask & (1 << p.bit_position)
        ]
        db_role = Role(name="tenant-admin", tenant_id=tenant_id, permission_mask=effective_mask)
        db_role.permissions = list(permission_rows)
        self.db.add(db_role)
        await self.db.flush()

        if permission_rows:
            await self.db.execute(
                insert(role_grantable_permissions),
                [{"role_id": db_role.id, "permission_id": perm.id} for perm in permission_rows],
            )
        await self.db.commit()
        await self.db.refresh(db_role)
        return await self.get_by_id(db_role.id)

    async def sync_root_tenant_role_permissions(
        self, tenant_id: uuid.UUID, allowed_permission_mask: int
    ) -> Role | None:
        """Re-syncs a tenant's bootstrap "tenant-admin" role (and what it's
        configured to grant) to a newly-edited ceiling — see
        `TenantService.update_tenant_permissions`. Only touches that one
        root role; any other role the tenant admin has since created keeps
        whatever it already holds, bounded going forward by the new ceiling
        via `RoleService.create_role`/`add_permission_to_role`, not
        retroactively stripped here. Returns None if the tenant has no such
        role (shouldn't happen outside hand-built test fixtures)."""
        from app.core.rbac.registry import SUPERUSER_ONLY_PERMISSIONS, TENANT_ROLE_MASK

        role = await self.db.scalar(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.tenant_id == tenant_id, Role.name == "tenant-admin")
        )
        if role is None:
            return None

        effective_mask = allowed_permission_mask & TENANT_ROLE_MASK
        all_rows = (
            await self.db.scalars(
                select(Permission).where(Permission.name.notin_(SUPERUSER_ONLY_PERMISSIONS))
            )
        ).all()
        permission_rows = [
            p for p in all_rows if p.bit_position is not None and effective_mask & (1 << p.bit_position)
        ]

        role.permissions = list(permission_rows)
        role.permission_mask = effective_mask
        await self.db.flush()

        await self.db.execute(
            delete(role_grantable_permissions).where(role_grantable_permissions.c.role_id == role.id)
        )
        if permission_rows:
            await self.db.execute(
                insert(role_grantable_permissions),
                [{"role_id": role.id, "permission_id": perm.id} for perm in permission_rows],
            )

        events = await self._bump_perm_version_for_role_holders(role.id)
        await self.db.commit()
        await self.db.refresh(role)
        await publish_events(events)
        return await self.get_by_id(role.id)

    async def update(self, role: Role, update_data: dict) -> Role:
        for key, value in update_data.items():
            setattr(role, key, value)
        await self.db.commit()
        await self.db.refresh(role)
        return await self.get_by_id(role.id)

    async def delete(self, role: Role) -> None:
        await self.db.delete(role)
        await self.db.commit()

    async def list_all(self, skip: int, limit: int):
        result = await self.db.scalars(
            select(Role).options(selectinload(Role.permissions)).offset(skip).limit(limit)
        )
        return result.unique().all()

    async def list_by_tenant(self, tenant_id: uuid.UUID, skip: int, limit: int):
        """A non-superuser's role list: their own tenant's roles plus any
        global (`tenant_id IS NULL`) roles — mirrors the access rule
        `RoleService._ensure_role_in_scope` already applies to single-role
        reads/writes, just as a list filter instead of a per-row check."""
        result = await self.db.scalars(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)))
            .offset(skip)
            .limit(limit)
        )
        return result.unique().all()

    async def assign_to_user(self, role_id: int, user_id: uuid.UUID) -> None:
        stmt = insert(user_roles).values(user_id=user_id, role_id=role_id)
        await self.db.execute(stmt)
        events = await self._bump_perm_version([user_id])
        await self.db.commit()
        await publish_events(events)

    async def remove_from_user(self, role_id: int, user_id: uuid.UUID) -> None:
        stmt = delete(user_roles).where(
            user_roles.c.user_id == user_id, user_roles.c.role_id == role_id
        )
        await self.db.execute(stmt)
        events = await self._bump_perm_version([user_id])
        await self.db.commit()
        await publish_events(events)

    async def user_has_role(self, user_id: uuid.UUID, role_id: int) -> bool:
        return bool(
            await self.db.scalar(
                select(exists().where(
                    user_roles.c.user_id == user_id, user_roles.c.role_id == role_id
                ))
            )
        )

    async def get_permission_by_id(self, permission_id: int) -> Permission | None:
        return await self.db.scalar(select(Permission).where(Permission.id == permission_id))

    async def add_permission(self, role: Role, permission: Permission) -> Role:
        role.permissions.append(permission)
        if permission.bit_position is not None:
            role.permission_mask = role.permission_mask | (1 << permission.bit_position)
        events = await self._bump_perm_version_for_role_holders(role.id)
        await self.db.commit()
        await self.db.refresh(role)
        await publish_events(events)
        return role

    async def remove_permission(self, role: Role, permission: Permission) -> Role:
        role.permissions.remove(permission)
        if permission.bit_position is not None:
            role.permission_mask = role.permission_mask & ~(1 << permission.bit_position)
        events = await self._bump_perm_version_for_role_holders(role.id)
        await self.db.commit()
        await self.db.refresh(role)
        await publish_events(events)
        return role

    # ------------------------------------------------------------------
    # Authz-cache staleness: bump `User.perm_version` for whoever might be
    # affected by a mutation, in the same (not-yet-committed) transaction,
    # then publish the resulting versions to Redis only after a successful
    # commit — never announce a version that might still roll back.
    # ------------------------------------------------------------------

    async def _bump_perm_version(self, user_ids: list[uuid.UUID]) -> list[dict]:
        if not user_ids:
            return []
        stmt = (
            update(User)
            .where(User.id.in_(user_ids))
            .values(perm_version=User.perm_version + 1)
            .returning(User.id, User.perm_version)
        )
        rows = (await self.db.execute(stmt)).all()
        return [{"type": "perm_version", "user_id": str(uid), "version": version} for uid, version in rows]

    async def _bump_perm_version_for_role_holders(self, role_id: int) -> list[dict]:
        stmt = (
            update(User)
            .where(User.id.in_(select(user_roles.c.user_id).where(user_roles.c.role_id == role_id)))
            .values(perm_version=User.perm_version + 1)
            .returning(User.id, User.perm_version)
        )
        rows = (await self.db.execute(stmt)).all()
        return [{"type": "perm_version", "user_id": str(uid), "version": version} for uid, version in rows]

    # ------------------------------------------------------------------
    # Grant delegation: which roles/permissions a holder of `role_id` may
    # hand out to other users.
    # ------------------------------------------------------------------

    async def grantable_role_link_exists(self, role_id: int, grantable_role_id: int) -> bool:
        return bool(
            await self.db.scalar(
                select(exists().where(
                    role_grantable_roles.c.role_id == role_id,
                    role_grantable_roles.c.grantable_role_id == grantable_role_id,
                ))
            )
        )

    async def add_grantable_role(self, role_id: int, grantable_role_id: int) -> None:
        stmt = insert(role_grantable_roles).values(
            role_id=role_id, grantable_role_id=grantable_role_id
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def remove_grantable_role(self, role_id: int, grantable_role_id: int) -> None:
        stmt = delete(role_grantable_roles).where(
            role_grantable_roles.c.role_id == role_id,
            role_grantable_roles.c.grantable_role_id == grantable_role_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def grantable_permission_link_exists(self, role_id: int, permission_id: int) -> bool:
        return bool(
            await self.db.scalar(
                select(exists().where(
                    role_grantable_permissions.c.role_id == role_id,
                    role_grantable_permissions.c.permission_id == permission_id,
                ))
            )
        )

    async def add_grantable_permission(self, role_id: int, permission_id: int) -> None:
        stmt = insert(role_grantable_permissions).values(
            role_id=role_id, permission_id=permission_id
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def remove_grantable_permission(self, role_id: int, permission_id: int) -> None:
        stmt = delete(role_grantable_permissions).where(
            role_grantable_permissions.c.role_id == role_id,
            role_grantable_permissions.c.permission_id == permission_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_grantable_role_ids(self, role_ids: list[int]) -> set[int]:
        if not role_ids:
            return set()
        result = await self.db.scalars(
            select(role_grantable_roles.c.grantable_role_id).where(
                role_grantable_roles.c.role_id.in_(role_ids)
            )
        )
        return set(result.all())

    async def get_grantable_permission_ids(self, role_ids: list[int]) -> set[int]:
        if not role_ids:
            return set()
        result = await self.db.scalars(
            select(role_grantable_permissions.c.permission_id).where(
                role_grantable_permissions.c.role_id.in_(role_ids)
            )
        )
        return set(result.all())

    async def get_grantable_permission_mask(self, role_ids: list[int]) -> int:
        """OR of the bit positions of every permission the given roles are
        configured to be able to grant — used by `RoleService.create_role`
        to bound what a non-superuser actor may put in a new role's mask."""
        if not role_ids:
            return 0
        result = await self.db.scalars(
            select(Permission.bit_position)
            .join(role_grantable_permissions, role_grantable_permissions.c.permission_id == Permission.id)
            .where(role_grantable_permissions.c.role_id.in_(role_ids))
        )
        mask = 0
        for bit in result.all():
            if bit is not None:
                mask |= 1 << bit
        return mask
