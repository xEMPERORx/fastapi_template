import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Ban, CheckCircle2, ShieldAlert } from 'lucide-react'
import { toast } from 'sonner'
import { tenantsApi, usersApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import { PageHeader } from '@/components/PageHeader'
import { PermissionCheckboxList } from '@/components/tenants/PermissionCheckboxList'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export function TenantDetailPage() {
  const { tenantId } = useParams<{ tenantId: string }>()
  const queryClient = useQueryClient()

  const tenantQuery = useQuery({
    queryKey: ['tenants', tenantId],
    queryFn: () => tenantsApi.get(tenantId!),
    enabled: !!tenantId,
  })

  const usersQuery = useQuery({
    queryKey: ['tenants', tenantId, 'users'],
    queryFn: () => usersApi.list(0, 100, tenantId),
    enabled: !!tenantId,
  })

  const setActive = useMutation({
    mutationFn: (active: boolean) =>
      active ? tenantsApi.activate(tenantId!) : tenantsApi.deactivate(tenantId!),
    onSuccess: (_data, active) => {
      toast.success(active ? 'Tenant activated' : 'Tenant deactivated')
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not update tenant')),
  })

  const [editedPermissions, setEditedPermissions] = useState<string[] | null>(null)
  useEffect(() => {
    if (tenantQuery.data && editedPermissions === null) {
      setEditedPermissions(tenantQuery.data.allowed_permissions)
    }
  }, [tenantQuery.data, editedPermissions])

  const updatePermissions = useMutation({
    mutationFn: (names: string[]) => tenantsApi.updatePermissions(tenantId!, names),
    onSuccess: (updated) => {
      toast.success("Tenant's permission ceiling updated")
      setEditedPermissions(updated.allowed_permissions)
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not update permissions')),
  })

  const permissionsDirty =
    editedPermissions !== null &&
    tenantQuery.data !== undefined &&
    (editedPermissions.length !== tenantQuery.data.allowed_permissions.length ||
      editedPermissions.some((name) => !tenantQuery.data!.allowed_permissions.includes(name)))

  if (tenantQuery.isLoading) {
    return (
      <div className="p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="mt-4 h-40 w-full" />
      </div>
    )
  }

  if (tenantQuery.isError || !tenantQuery.data) {
    return (
      <div className="p-6 text-sm text-muted-foreground">
        Couldn't load this tenant.{' '}
        <Link to="/tenants" className="underline">
          Back to tenants
        </Link>
      </div>
    )
  }

  const tenant = tenantQuery.data
  const users = usersQuery.data ?? []

  return (
    <>
      <PageHeader
        title={tenant.name}
        description={tenant.id}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={setActive.isPending}
              onClick={() => setActive.mutate(!tenant.is_active)}
            >
              {tenant.is_active ? <Ban /> : <CheckCircle2 />}
              {tenant.is_active ? 'Deactivate' : 'Activate'}
            </Button>
            <Button variant="outline" size="sm" render={<Link to="/tenants" />}>
              <ArrowLeft />
              Back
            </Button>
          </div>
        }
      />

      <div className="flex flex-col gap-6 p-6">
        <div className="flex flex-wrap gap-2">
          <Badge variant={tenant.is_active ? 'default' : 'destructive'}>
            {tenant.is_active ? 'Active' : 'Deactivated'}
          </Badge>
        </div>

        <section className="flex flex-col gap-3">
          <div>
            <h2 className="text-sm font-semibold">Permission ceiling</h2>
            <p className="text-xs text-muted-foreground">
              What this tenant's roles may ever hold. The tenant admin only sees and grants
              permissions from within this set — narrowing it here doesn't retroactively strip
              permissions already assigned to a role, only bounds new ones going forward.
            </p>
          </div>
          <PermissionCheckboxList
            selected={editedPermissions ?? []}
            onChange={setEditedPermissions}
          />
          <div>
            <Button
              size="sm"
              disabled={!permissionsDirty || updatePermissions.isPending}
              onClick={() => editedPermissions && updatePermissions.mutate(editedPermissions)}
            >
              Save permission ceiling
            </Button>
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold">Users ({users.length})</h2>
          <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Roles</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usersQuery.isLoading &&
                  Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                      <TableCell colSpan={3}>
                        <Skeleton className="h-9 w-full" />
                      </TableCell>
                    </TableRow>
                  ))}

                {!usersQuery.isLoading && users.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} className="py-8 text-center text-sm text-muted-foreground">
                      No users in this tenant.
                    </TableCell>
                  </TableRow>
                )}

                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div className="font-medium text-foreground">{user.username}</div>
                      <div className="text-xs text-muted-foreground">{user.email}</div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {user.roles.length === 0 && (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                        {user.roles.map((role) => (
                          <Badge key={role} variant="outline">
                            {role}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        <Badge variant={user.is_verified ? 'default' : 'outline'}>
                          {user.is_verified ? 'Verified' : 'Unverified'}
                        </Badge>
                        {!user.is_active && <Badge variant="destructive">Deactivated</Badge>}
                        {user.is_superuser && (
                          <Badge variant="secondary" className="gap-1">
                            <ShieldAlert className="size-3" />
                            superuser
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>
      </div>
    </>
  )
}
