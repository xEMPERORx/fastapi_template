import { api } from './api'
import type {
  GrantableSummary,
  Permission,
  Role,
  RoleGrants,
  Tenant,
  TenantWithAdmin,
  TokenResponse,
  UserCount,
  UserDetail,
  UserListItem,
  UserResponse,
} from './types'

export const authApi = {
  login: async (username: string, password: string): Promise<TokenResponse> => {
    const form = new URLSearchParams()
    form.set('username', username)
    form.set('password', password)
    const { data } = await api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },
  me: async (): Promise<UserResponse> => {
    const { data } = await api.get<UserResponse>('/auth/user')
    return data
  },
  logout: async (): Promise<void> => {
    await api.post('/auth/logout')
  },
}

export const usersApi = {
  list: async (skip: number, limit: number, tenantId?: string): Promise<UserListItem[]> => {
    const { data } = await api.get<UserListItem[]>('/users/', {
      params: { skip, limit, tenant_id: tenantId },
    })
    return data
  },
  count: async (tenantId?: string): Promise<UserCount> => {
    const { data } = await api.get<UserCount>('/users/count', { params: { tenant_id: tenantId } })
    return data
  },
  create: async (username: string, email: string, password: string): Promise<UserListItem> => {
    const { data } = await api.post<UserListItem>('/users/', { username, email, password })
    return data
  },
  get: async (userId: string): Promise<UserDetail> => {
    const { data } = await api.get<UserDetail>(`/users/${userId}`)
    return data
  },
  myGrants: async (): Promise<GrantableSummary> => {
    const { data } = await api.get<GrantableSummary>('/users/me/grants')
    return data
  },
  assignRole: async (userId: string, roleId: number): Promise<void> => {
    await api.post(`/users/${userId}/roles/${roleId}`)
  },
  removeRole: async (userId: string, roleId: number): Promise<void> => {
    await api.delete(`/users/${userId}/roles/${roleId}`)
  },
  grantPermission: async (userId: string, permissionId: number): Promise<void> => {
    await api.post(`/users/${userId}/permissions/${permissionId}`)
  },
  revokePermission: async (userId: string, permissionId: number): Promise<void> => {
    await api.delete(`/users/${userId}/permissions/${permissionId}`)
  },
  deactivate: async (userId: string): Promise<void> => {
    await api.post(`/users/${userId}/deactivate`)
  },
  activate: async (userId: string): Promise<void> => {
    await api.post(`/users/${userId}/activate`)
  },
}

export const rolesApi = {
  list: async (skip = 0, limit = 100): Promise<Role[]> => {
    const { data } = await api.get<Role[]>('/role/', { params: { skip, limit } })
    return data
  },
  create: async (name: string): Promise<Role> => {
    const { data } = await api.post<Role>('/role/', { name })
    return data
  },
  update: async (roleId: number, name: string): Promise<Role> => {
    const { data } = await api.put<Role>(`/role/${roleId}`, { name })
    return data
  },
  getGrants: async (roleId: number): Promise<RoleGrants> => {
    const { data } = await api.get<RoleGrants>(`/role/${roleId}/grants`)
    return data
  },
  remove: async (roleId: number): Promise<void> => {
    await api.delete(`/role/${roleId}`)
  },
  addPermission: async (roleId: number, permissionId: number): Promise<Role> => {
    const { data } = await api.post<Role>(`/role/${roleId}/permissions/${permissionId}`)
    return data
  },
  removePermission: async (roleId: number, permissionId: number): Promise<Role> => {
    const { data } = await api.delete<Role>(`/role/${roleId}/permissions/${permissionId}`)
    return data
  },
  addGrantableRole: async (roleId: number, grantableRoleId: number): Promise<void> => {
    await api.post(`/role/${roleId}/grantable-roles/${grantableRoleId}`)
  },
  removeGrantableRole: async (roleId: number, grantableRoleId: number): Promise<void> => {
    await api.delete(`/role/${roleId}/grantable-roles/${grantableRoleId}`)
  },
  addGrantablePermission: async (roleId: number, permissionId: number): Promise<void> => {
    await api.post(`/role/${roleId}/grantable-permissions/${permissionId}`)
  },
  removeGrantablePermission: async (roleId: number, permissionId: number): Promise<void> => {
    await api.delete(`/role/${roleId}/grantable-permissions/${permissionId}`)
  },
}

export const tenantsApi = {
  list: async (skip = 0, limit = 100): Promise<Tenant[]> => {
    const { data } = await api.get<Tenant[]>('/tenants/', { params: { skip, limit } })
    return data
  },
  create: async (
    name: string,
    adminUsername: string,
    adminEmail: string,
    adminPassword: string,
    allowedPermissions?: string[],
  ): Promise<TenantWithAdmin> => {
    const { data } = await api.post<TenantWithAdmin>('/tenants/', {
      name,
      admin_username: adminUsername,
      admin_email: adminEmail,
      admin_password: adminPassword,
      allowed_permissions: allowedPermissions,
    })
    return data
  },
  get: async (tenantId: string): Promise<Tenant> => {
    const { data } = await api.get<Tenant>(`/tenants/${tenantId}`)
    return data
  },
  activate: async (tenantId: string): Promise<void> => {
    await api.post(`/tenants/${tenantId}/activate`)
  },
  deactivate: async (tenantId: string): Promise<void> => {
    await api.post(`/tenants/${tenantId}/deactivate`)
  },
  updatePermissions: async (tenantId: string, allowedPermissions: string[]): Promise<Tenant> => {
    const { data } = await api.patch<Tenant>(`/tenants/${tenantId}/permissions`, {
      allowed_permissions: allowedPermissions,
    })
    return data
  },
}

// Permissions are a fixed, code-defined catalog (`app.core.rbac.registry`) —
// deliberately no create/update/delete route on the backend (see
// `app/api/v1/routes/rbac/permission.py`'s own comment on why). Read-only
// here to match.
export const permissionsApi = {
  list: async (skip = 0, limit = 100): Promise<Permission[]> => {
    const { data } = await api.get<Permission[]>('/permission/', { params: { skip, limit } })
    return data
  },
}
