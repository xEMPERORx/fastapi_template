from app.core.logger import LoggedService
from app.core.rbac.registry import TENANT_ROLE_MASK, mask_for
from app.error.auth import UserMailExist, UsernameExist
from app.error.rbac import SuperuserRequired
from app.error.tenant import TenantExists, TenantNotFound
from app.models.db_model import Tenant, User
from app.repositories.auth.user import UserRepository
from app.repositories.rbac.role import RoleRepository
from app.repositories.tenant.tenant import TenantRepository
from app.schema.tenant import TenantCreate
from app.services.auth.password import get_password_hash


class TenantService(LoggedService):
    def __init__(
        self,
        tenant_repo: TenantRepository,
        role_repo: RoleRepository,
        user_repo: UserRepository,
    ):
        self.tenant_repo = tenant_repo
        self.role_repo = role_repo
        self.user_repo = user_repo

    async def create_tenant_with_admin(self, actor: User, data: TenantCreate) -> dict:
        """Bootstraps a new tenant: the tenant row itself, a "tenant-admin"
        root role scoped to it (every catalog permission, and able to grant
        every catalog permission to others — see
        `RoleRepository.create_root_tenant_role`), and the tenant's first
        admin user holding that role.

        Restricted to a real superuser (`superuser_required()` at the route,
        re-checked here as defense in depth, same as every other actor-gated
        service method in this codebase) — never reachable via any catalog
        permission, since a tenant boundary is a bigger blast radius than
        anything a `role:*`/`user:*` permission should be able to touch.
        """
        if not actor.is_superuser:
            raise SuperuserRequired()

        if await self.tenant_repo.get_by_name(data.name):
            raise TenantExists(data.name)
        if await self.user_repo.exists_by_username(data.admin_username):
            raise UsernameExist(data.admin_username)
        if await self.user_repo.exists_by_email(data.admin_email):
            raise UserMailExist(data.admin_email)

        allowed_mask = (
            mask_for(data.allowed_permissions) if data.allowed_permissions is not None else TENANT_ROLE_MASK
        ) & TENANT_ROLE_MASK

        tenant = await self.tenant_repo.create(data.name, allowed_permission_mask=allowed_mask)
        admin_role = await self.role_repo.create_root_tenant_role(tenant.id, allowed_mask)
        admin_user = await self.user_repo.create(
            username=data.admin_username,
            email=data.admin_email,
            password=get_password_hash(data.admin_password),
            is_verified=True,
            tenant_id=tenant.id,
            created_by_id=actor.id,
        )
        await self.role_repo.assign_to_user(admin_role.id, admin_user.id)

        return {"tenant": tenant, "admin": admin_user}

    async def get_tenant(self, tenant_id) -> Tenant:
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFound(tenant_id)
        return tenant

    async def list_tenants(self, skip: int, limit: int) -> list[Tenant]:
        return await self.tenant_repo.list_all(skip, limit)

    async def set_tenant_active(self, actor: User, tenant_id, is_active: bool) -> Tenant:
        if not actor.is_superuser:
            raise SuperuserRequired()
        tenant = await self.get_tenant(tenant_id)
        return await self.tenant_repo.set_active(tenant, is_active)

    async def update_tenant_permissions(self, actor: User, tenant_id, allowed_permissions: list[str]) -> Tenant:
        """Superuser-only: raise or lower a tenant's permission ceiling after
        creation. Also re-syncs the tenant's bootstrap "tenant-admin" role to
        the new mask (see `RoleRepository.sync_root_tenant_role_permissions`)
        so raising the ceiling is immediately usable, not just recorded —
        without that, a superuser widening a tenant's ceiling would have no
        visible effect until someone separately edited the root role by hand.
        """
        if not actor.is_superuser:
            raise SuperuserRequired()
        tenant = await self.get_tenant(tenant_id)
        allowed_mask = mask_for(allowed_permissions) & TENANT_ROLE_MASK
        tenant = await self.tenant_repo.set_allowed_permission_mask(tenant, allowed_mask)
        await self.role_repo.sync_root_tenant_role_permissions(tenant.id, allowed_mask)
        return tenant
