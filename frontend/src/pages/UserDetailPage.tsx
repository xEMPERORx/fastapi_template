import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Ban, CheckCircle2, Plus, ShieldAlert, X } from 'lucide-react'
import { toast } from 'sonner'
import { usersApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import { PageHeader } from '@/components/PageHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export function UserDetailPage() {
  const { userId } = useParams<{ userId: string }>()
  const queryClient = useQueryClient()

  const userQuery = useQuery({
    queryKey: ['users', userId],
    queryFn: () => usersApi.get(userId!),
    enabled: !!userId,
  })

  const grantsQuery = useQuery({
    queryKey: ['users', 'me', 'grants'],
    queryFn: () => usersApi.myGrants(),
  })

  const [selectedRoleId, setSelectedRoleId] = useState<string>('')
  const [selectedPermissionId, setSelectedPermissionId] = useState<string>('')

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ['users', userId] })
  }

  const assignRole = useMutation({
    mutationFn: (roleId: number) => usersApi.assignRole(userId!, roleId),
    onSuccess: () => {
      toast.success('Role assigned')
      setSelectedRoleId('')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not assign role')),
  })

  const removeRole = useMutation({
    mutationFn: (roleId: number) => usersApi.removeRole(userId!, roleId),
    onSuccess: () => {
      toast.success('Role removed')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not remove role')),
  })

  const grantPermission = useMutation({
    mutationFn: (permissionId: number) => usersApi.grantPermission(userId!, permissionId),
    onSuccess: () => {
      toast.success('Permission granted')
      setSelectedPermissionId('')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not grant permission')),
  })

  const revokePermission = useMutation({
    mutationFn: (permissionId: number) => usersApi.revokePermission(userId!, permissionId),
    onSuccess: () => {
      toast.success('Permission revoked')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not revoke permission')),
  })

  const setActive = useMutation({
    mutationFn: (active: boolean) => (active ? usersApi.activate(userId!) : usersApi.deactivate(userId!)),
    onSuccess: (_data, active) => {
      toast.success(active ? 'User activated' : 'User deactivated')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not update user')),
  })

  if (userQuery.isLoading) {
    return (
      <div className="p-6">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="mt-4 h-40 w-full" />
      </div>
    )
  }

  if (userQuery.isError || !userQuery.data) {
    return (
      <div className="p-6 text-sm text-muted-foreground">
        Couldn't load this user.{' '}
        <Link to="/users" className="underline">
          Back to users
        </Link>
      </div>
    )
  }

  const user = userQuery.data
  const grants = grantsQuery.data

  // Roles/permissions the logged-in admin is allowed to hand out, minus
  // whatever this user already has — the backend re-checks on every mutating
  // call regardless, this is purely to keep the UI from offering choices
  // that would just 403.
  const assignableRoles =
    grants?.grantable_roles.filter((r) => !user.roles.includes(r.name)) ?? []
  const grantablePermissions =
    grants?.grantable_permissions.filter((p) => !user.permissions.includes(p.name)) ?? []
  const canDeactivateUser = grants?.effective_permissions.includes('user:deactivate') ?? false

  return (
    <>
      <PageHeader
        title={user.username}
        description={user.email}
        actions={
          <div className="flex items-center gap-2">
            {canDeactivateUser && !user.is_superuser && (
              <Button
                variant="outline"
                size="sm"
                disabled={setActive.isPending}
                onClick={() => setActive.mutate(!user.is_active)}
              >
                {user.is_active ? <Ban /> : <CheckCircle2 />}
                {user.is_active ? 'Deactivate' : 'Activate'}
              </Button>
            )}
            <Button variant="outline" size="sm" render={<Link to="/users" />}>
              <ArrowLeft />
              Back
            </Button>
          </div>
        }
      />

      <div className="flex flex-col gap-6 p-6">
        <div className="flex flex-wrap gap-2">
          <Badge variant={user.is_verified ? 'default' : 'outline'}>
            {user.is_verified ? 'Verified' : 'Unverified'}
          </Badge>
          {!user.is_active && <Badge variant="destructive">Deactivated</Badge>}
          {user.is_superuser && (
            <Badge variant="secondary" className="gap-1">
              <ShieldAlert className="size-3" />
              Superuser — bypasses all permission checks
            </Badge>
          )}
        </div>

        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold">Roles</h2>
          <div className="flex flex-wrap gap-2">
            {user.roles.length === 0 && (
              <p className="text-sm text-muted-foreground">No roles assigned.</p>
            )}
            {user.roles.map((role) => (
              <Badge key={role} variant="outline" className="gap-1 py-1 pr-1">
                {role}
                <button
                  type="button"
                  aria-label={`Remove role ${role}`}
                  className="rounded-full p-0.5 hover:bg-muted"
                  disabled={removeRole.isPending}
                  onClick={() => {
                    const roleId = grants?.grantable_roles.find((r) => r.name === role)?.id
                    if (roleId) removeRole.mutate(roleId)
                    else toast.error("You don't have permission to remove this role.")
                  }}
                >
                  <X className="size-3" />
                </button>
              </Badge>
            ))}
          </div>

          {assignableRoles.length > 0 && (
            <div className="flex items-center gap-2">
              <Select value={selectedRoleId} onValueChange={(value) => setSelectedRoleId(value ?? '')}>
                <SelectTrigger className="w-56">
                  <SelectValue placeholder="Assign a role..." />
                </SelectTrigger>
                <SelectContent>
                  {assignableRoles.map((role) => (
                    <SelectItem key={role.id} value={String(role.id)}>
                      {role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                size="sm"
                disabled={!selectedRoleId || assignRole.isPending}
                onClick={() => assignRole.mutate(Number(selectedRoleId))}
              >
                <Plus />
                Assign
              </Button>
            </div>
          )}
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold">Direct permissions</h2>
          <p className="text-xs text-muted-foreground">
            Granted straight to this user, independent of their roles.
          </p>
          <div className="flex flex-wrap gap-2">
            {user.permissions.length === 0 && (
              <p className="text-sm text-muted-foreground">No direct permissions.</p>
            )}
            {user.permissions.map((permission) => (
              <Badge key={permission} variant="outline" className="gap-1 py-1 pr-1">
                {permission}
                <button
                  type="button"
                  aria-label={`Revoke permission ${permission}`}
                  className="rounded-full p-0.5 hover:bg-muted"
                  disabled={revokePermission.isPending}
                  onClick={() => {
                    const permissionId = grants?.grantable_permissions.find(
                      (p) => p.name === permission,
                    )?.id
                    if (permissionId) revokePermission.mutate(permissionId)
                    else toast.error("You don't have permission to revoke this.")
                  }}
                >
                  <X className="size-3" />
                </button>
              </Badge>
            ))}
          </div>

          {grantablePermissions.length > 0 && (
            <div className="flex items-center gap-2">
              <Select
                value={selectedPermissionId}
                onValueChange={(value) => setSelectedPermissionId(value ?? '')}
              >
                <SelectTrigger className="w-56">
                  <SelectValue placeholder="Grant a permission..." />
                </SelectTrigger>
                <SelectContent>
                  {grantablePermissions.map((permission) => (
                    <SelectItem key={permission.id} value={String(permission.id)}>
                      {permission.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                size="sm"
                disabled={!selectedPermissionId || grantPermission.isPending}
                onClick={() => grantPermission.mutate(Number(selectedPermissionId))}
              >
                <Plus />
                Grant
              </Button>
            </div>
          )}
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold">Effective permissions</h2>
          <p className="text-xs text-muted-foreground">
            The full set this user can act on — from roles and direct grants combined.
          </p>
          <div className="flex flex-wrap gap-1.5">
            {user.effective_permissions.length === 0 && (
              <p className="text-sm text-muted-foreground">None.</p>
            )}
            {user.effective_permissions.map((permission) => (
              <Badge key={permission} variant="secondary">
                {permission}
              </Badge>
            ))}
          </div>
        </section>
      </div>
    </>
  )
}
