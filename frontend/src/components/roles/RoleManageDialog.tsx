import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { permissionsApi, rolesApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import type { Role } from '@/lib/types'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

function GrantList({
  title,
  hint,
  items,
  options,
  onAdd,
  onRemove,
  pending,
}: {
  title: string
  hint: string
  items: string[]
  options: { id: number; name: string }[]
  onAdd: (id: number) => void
  onRemove: (name: string) => void
  pending: boolean
}) {
  const [selected, setSelected] = useState('')
  const available = options.filter((o) => !items.includes(o.name))

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h3 className="text-sm font-medium">{title}</h3>
        <p className="text-xs text-muted-foreground">{hint}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {items.length === 0 && <p className="text-sm text-muted-foreground">None yet.</p>}
        {items.map((name) => (
          <Badge key={name} variant="outline" className="gap-1 py-1 pr-1">
            {name}
            <button
              type="button"
              aria-label={`Remove ${name}`}
              className="rounded-full p-0.5 hover:bg-muted"
              disabled={pending}
              onClick={() => onRemove(name)}
            >
              <X className="size-3" />
            </button>
          </Badge>
        ))}
      </div>

      {available.length > 0 && (
        <div className="flex items-center gap-2">
          <Select value={selected} onValueChange={(value) => setSelected(value ?? '')}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Add..." />
            </SelectTrigger>
            <SelectContent>
              {available.map((o) => (
                <SelectItem key={o.id} value={String(o.id)}>
                  {o.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            size="sm"
            disabled={!selected || pending}
            onClick={() => {
              onAdd(Number(selected))
              setSelected('')
            }}
          >
            <Plus />
            Add
          </Button>
        </div>
      )}
    </div>
  )
}

export function RoleManageDialog({
  role,
  open,
  onOpenChange,
}: {
  role: Role
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()

  const rolesQuery = useQuery({ queryKey: ['roles'], queryFn: () => rolesApi.list() })
  const permissionsQuery = useQuery({
    queryKey: ['permissions'],
    queryFn: () => permissionsApi.list(),
  })
  const grantsQuery = useQuery({
    queryKey: ['role', role.id, 'grants'],
    queryFn: () => rolesApi.getGrants(role.id),
  })

  function invalidateAll() {
    queryClient.invalidateQueries({ queryKey: ['roles'] })
    queryClient.invalidateQueries({ queryKey: ['role', role.id, 'grants'] })
  }

  const permissionIdByName = new Map(permissionsQuery.data?.map((p) => [p.name, p.id]))
  const roleIdByName = new Map(rolesQuery.data?.map((r) => [r.name, r.id]))

  const addPermission = useMutation({
    mutationFn: (permissionId: number) => rolesApi.addPermission(role.id, permissionId),
    onSuccess: () => {
      toast.success('Permission added to role')
      invalidateAll()
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  })
  const removePermission = useMutation({
    mutationFn: (permissionId: number) => rolesApi.removePermission(role.id, permissionId),
    onSuccess: () => {
      toast.success('Permission removed from role')
      invalidateAll()
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  })

  const addGrantableRole = useMutation({
    mutationFn: (grantableRoleId: number) => rolesApi.addGrantableRole(role.id, grantableRoleId),
    onSuccess: () => {
      toast.success('Delegation updated')
      invalidateAll()
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  })
  const removeGrantableRole = useMutation({
    mutationFn: (grantableRoleId: number) =>
      rolesApi.removeGrantableRole(role.id, grantableRoleId),
    onSuccess: () => {
      toast.success('Delegation updated')
      invalidateAll()
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  })

  const addGrantablePermission = useMutation({
    mutationFn: (permissionId: number) => rolesApi.addGrantablePermission(role.id, permissionId),
    onSuccess: () => {
      toast.success('Delegation updated')
      invalidateAll()
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  })
  const removeGrantablePermission = useMutation({
    mutationFn: (permissionId: number) =>
      rolesApi.removeGrantablePermission(role.id, permissionId),
    onSuccess: () => {
      toast.success('Delegation updated')
      invalidateAll()
    },
    onError: (err) => toast.error(apiErrorMessage(err)),
  })

  const otherRoles = (rolesQuery.data ?? []).filter((r) => r.id !== role.id)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{role.name}</DialogTitle>
          <DialogDescription>
            Configure what this role does, and what its holders may hand out to others.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="permissions">
          <TabsList>
            <TabsTrigger value="permissions">Permissions</TabsTrigger>
            <TabsTrigger value="grant-roles">Can grant roles</TabsTrigger>
            <TabsTrigger value="grant-permissions">Can grant permissions</TabsTrigger>
          </TabsList>

          <TabsContent value="permissions" className="pt-4">
            <GrantList
              title="Role permissions"
              hint="What this role itself grants to anyone who holds it."
              items={role.permissions}
              options={permissionsQuery.data ?? []}
              pending={addPermission.isPending || removePermission.isPending}
              onAdd={(id) => addPermission.mutate(id)}
              onRemove={(name) => {
                const id = permissionIdByName.get(name)
                if (id) removePermission.mutate(id)
              }}
            />
          </TabsContent>

          <TabsContent value="grant-roles" className="pt-4">
            <GrantList
              title="Delegatable roles"
              hint="Roles that a holder of this role is allowed to assign to other users."
              items={grantsQuery.data?.grantable_roles ?? []}
              options={otherRoles}
              pending={addGrantableRole.isPending || removeGrantableRole.isPending}
              onAdd={(id) => addGrantableRole.mutate(id)}
              onRemove={(name) => {
                const id = roleIdByName.get(name)
                if (id) removeGrantableRole.mutate(id)
              }}
            />
          </TabsContent>

          <TabsContent value="grant-permissions" className="pt-4">
            <GrantList
              title="Delegatable permissions"
              hint="Permissions that a holder of this role is allowed to grant directly to a user."
              items={grantsQuery.data?.grantable_permissions ?? []}
              options={permissionsQuery.data ?? []}
              pending={addGrantablePermission.isPending || removeGrantablePermission.isPending}
              onAdd={(id) => addGrantablePermission.mutate(id)}
              onRemove={(name) => {
                const id = permissionIdByName.get(name)
                if (id) removeGrantablePermission.mutate(id)
              }}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
