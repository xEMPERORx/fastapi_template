import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowRight, Building2, ShieldCheck, Users } from 'lucide-react'
import { useAuthStore } from '@/lib/auth-store'
import { rolesApi, tenantsApi, usersApi } from '@/lib/endpoints'
import { PageHeader } from '@/components/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

function StatCard({
  label,
  value,
  icon: Icon,
  loading,
}: {
  label: string
  value: number
  icon: typeof Users
  loading: boolean
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted text-muted-foreground">
          <Icon className="size-5" />
        </div>
        <div className="flex min-w-0 flex-col">
          <span className="text-xs text-muted-foreground">{label}</span>
          {loading ? (
            <Skeleton className="mt-1 h-7 w-12" />
          ) : (
            <span className="text-2xl font-semibold tabular-nums tracking-tight">{value}</span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function SuperuserDashboard() {
  const { data: tenants, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => tenantsApi.list(),
  })
  const activeCount = tenants?.filter((t) => t.is_active).length ?? 0
  const inactiveCount = (tenants?.length ?? 0) - activeCount
  const recent = tenants?.slice(0, 5) ?? []

  return (
    <>
      <PageHeader
        title="Overview"
        description="Every organization on this deployment, at a glance."
        actions={
          <Button size="sm" render={<Link to="/tenants" />}>
            Manage tenants
            <ArrowRight />
          </Button>
        }
      />
      <div className="flex flex-col gap-6 p-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatCard label="Total tenants" value={tenants?.length ?? 0} icon={Building2} loading={isLoading} />
          <StatCard label="Active" value={activeCount} icon={Building2} loading={isLoading} />
          <StatCard label="Deactivated" value={inactiveCount} icon={Building2} loading={isLoading} />
        </div>

        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Recent tenants</h2>
            {tenants && tenants.length > 5 && (
              <Link to="/tenants" className="text-xs text-muted-foreground hover:text-foreground hover:underline">
                View all {tenants.length}
              </Link>
            )}
          </div>
          {isLoading ? (
            <Skeleton className="h-32 w-full rounded-xl" />
          ) : recent.length === 0 ? (
            <Card>
              <CardContent className="py-10 text-center">
                <p className="text-sm text-muted-foreground">No tenants yet.</p>
                <Button size="sm" className="mt-3" render={<Link to="/tenants" />}>
                  Create your first tenant
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
              {recent.map((tenant) => (
                <Link
                  key={tenant.id}
                  to={`/tenants/${tenant.id}`}
                  className="flex items-center justify-between border-b border-border px-4 py-3 text-sm outline-none last:border-b-0 hover:bg-muted/50 focus-visible:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset transition-colors duration-150"
                >
                  <span className="font-medium">{tenant.name}</span>
                  <Badge variant={tenant.is_active ? 'default' : 'outline'}>
                    {tenant.is_active ? 'Active' : 'Deactivated'}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  )
}

function TenantDashboard() {
  const tenantName = useAuthStore((s) => s.user?.tenant_name)

  const usersQuery = useQuery({ queryKey: ['users', 0], queryFn: () => usersApi.list(0, 5) })
  const countQuery = useQuery({ queryKey: ['users', 'count'], queryFn: () => usersApi.count() })
  const rolesQuery = useQuery({ queryKey: ['roles'], queryFn: () => rolesApi.list() })
  const grantsQuery = useQuery({ queryKey: ['users', 'me', 'grants'], queryFn: () => usersApi.myGrants() })
  const canCreateUser = grantsQuery.data?.effective_permissions.includes('user:create') ?? false

  const recent = usersQuery.data ?? []
  const totalUsers = countQuery.data?.count ?? 0

  return (
    <>
      <PageHeader
        title="Overview"
        description={tenantName ? `${tenantName} — accounts, roles, and permissions.` : 'Accounts, roles, and permissions.'}
        actions={
          <Button size="sm" render={<Link to="/users" />}>
            Manage users
            <ArrowRight />
          </Button>
        }
      />
      <div className="flex flex-col gap-6 p-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <StatCard label="Users" value={totalUsers} icon={Users} loading={countQuery.isLoading} />
          <StatCard label="Roles" value={rolesQuery.data?.length ?? 0} icon={ShieldCheck} loading={rolesQuery.isLoading} />
        </div>

        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Recent users</h2>
            <div className="flex items-center gap-3">
              {canCreateUser && (
                <Link to="/users" className="text-xs text-muted-foreground hover:text-foreground hover:underline">
                  New user
                </Link>
              )}
              {totalUsers > 5 && (
                <Link to="/users" className="text-xs text-muted-foreground hover:text-foreground hover:underline">
                  View all
                </Link>
              )}
            </div>
          </div>
          {usersQuery.isLoading ? (
            <Skeleton className="h-32 w-full rounded-xl" />
          ) : recent.length === 0 ? (
            <Card>
              <CardContent className="py-10 text-center">
                <p className="text-sm text-muted-foreground">No users yet.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
              {recent.map((user) => (
                <Link
                  key={user.id}
                  to={`/users/${user.id}`}
                  className="flex items-center justify-between border-b border-border px-4 py-3 text-sm outline-none last:border-b-0 hover:bg-muted/50 focus-visible:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:ring-inset transition-colors duration-150"
                >
                  <div className="flex min-w-0 flex-col">
                    <span className="font-medium">{user.username}</span>
                    <span className="truncate text-xs text-muted-foreground">{user.email}</span>
                  </div>
                  <div className="flex flex-wrap justify-end gap-1">
                    {user.roles.length === 0 ? (
                      <span className="text-xs text-muted-foreground">No roles</span>
                    ) : (
                      user.roles.map((role) => (
                        <Badge key={role} variant="outline">
                          {role}
                        </Badge>
                      ))
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  )
}

export function DashboardPage() {
  const isSuperuser = useAuthStore((s) => s.user?.is_superuser)
  return isSuperuser ? <SuperuserDashboard /> : <TenantDashboard />
}
