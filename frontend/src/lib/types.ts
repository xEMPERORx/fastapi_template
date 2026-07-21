export interface UserResponse {
  id: string
  username: string
  email: string
  tenant_id: string | null
  tenant_name: string | null
  is_superuser: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserListItem {
  id: string
  username: string
  email: string
  is_verified: boolean
  is_superuser: boolean
  is_active: boolean
  created_by_id: string | null
  roles: string[]
}

export interface UserDetail extends UserListItem {
  permissions: string[]
  effective_permissions: string[]
}

export interface RoleSummary {
  id: number
  name: string
}

export interface PermissionSummary {
  id: number
  name: string
}

export interface GrantableSummary {
  is_superuser: boolean
  effective_permissions: string[]
  grantable_roles: RoleSummary[]
  grantable_permissions: PermissionSummary[]
}

export interface Role {
  id: number
  name: string
  permissions: string[]
}

export interface RoleGrants {
  grantable_roles: string[]
  grantable_permissions: string[]
}

export interface Permission {
  id: number
  name: string
}

export interface UserCount {
  count: number
}

export interface Tenant {
  id: string
  name: string
  is_active: boolean
  allowed_permissions: string[]
}

export interface TenantAdmin {
  id: string
  username: string
  email: string
}

export interface TenantWithAdmin {
  tenant: Tenant
  admin: TenantAdmin
}

export interface ApiErrorBody {
  status: string
  message: string
  error_code: string
  technical_details?: string | null
}
