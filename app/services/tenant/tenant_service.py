from app.core.logger import LoggedService
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

        tenant = await self.tenant_repo.create(data.name)
        admin_role = await self.role_repo.create_root_tenant_role(tenant.id)
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
