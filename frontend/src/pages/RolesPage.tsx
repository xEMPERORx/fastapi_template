import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Settings2, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { rolesApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import type { Role } from '@/lib/types'
import { PageHeader } from '@/components/PageHeader'
import { RoleManageDialog } from '@/components/roles/RoleManageDialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export function RolesPage() {
  const queryClient = useQueryClient()
  const { data: roles, isLoading } = useQuery({ queryKey: ['roles'], queryFn: () => rolesApi.list() })

  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState('')
  const [manageRole, setManageRole] = useState<Role | null>(null)

  const createRole = useMutation({
    mutationFn: (name: string) => rolesApi.create(name),
    onSuccess: () => {
      toast.success('Role created')
      setNewName('')
      setCreateOpen(false)
      queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not create role')),
  })

  const deleteRole = useMutation({
    mutationFn: (roleId: number) => rolesApi.remove(roleId),
    onSuccess: () => {
      toast.success('Role deleted')
      queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not delete role')),
  })

  function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (newName.trim()) createRole.mutate(newName.trim())
  }

  // Keep the manage dialog's role data fresh as the underlying query refetches.
  const activeRole = manageRole ? (roles?.find((r) => r.id === manageRole.id) ?? manageRole) : null

  return (
    <>
      <PageHeader
        title="Roles"
        description="Roles bundle permissions and decide what their holders may delegate."
        actions={
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger render={<Button size="sm" />}>
              <Plus />
              New role
            </DialogTrigger>
            <DialogContent className="sm:max-w-sm">
              <form onSubmit={handleCreate}>
                <DialogHeader>
                  <DialogTitle>New role</DialogTitle>
                  <DialogDescription>
                    You can configure its permissions and delegation rules after creating it.
                  </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-1.5 py-4">
                  <Label htmlFor="role-name">Name</Label>
                  <Input
                    id="role-name"
                    autoFocus
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. manager"
                    required
                  />
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={createRole.isPending || !newName.trim()}>
                    Create role
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="p-6">
        <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Role</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead className="w-24" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={3}>
                      <Skeleton className="h-9 w-full" />
                    </TableCell>
                  </TableRow>
                ))}

              {!isLoading && roles?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="py-8 text-center text-sm text-muted-foreground">
                    No roles yet.
                  </TableCell>
                </TableRow>
              )}

              {roles?.map((role) => (
                <TableRow key={role.id}>
                  <TableCell className="font-medium">{role.name}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {role.permissions.length === 0 && (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                      {role.permissions.map((p) => (
                        <Badge key={p} variant="outline">
                          {p}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="icon-sm" onClick={() => setManageRole(role)}>
                        <Settings2 />
                        <span className="sr-only">Manage {role.name}</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        disabled={deleteRole.isPending}
                        onClick={() => {
                          if (confirm(`Delete role "${role.name}"?`)) deleteRole.mutate(role.id)
                        }}
                      >
                        <Trash2 />
                        <span className="sr-only">Delete {role.name}</span>
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {activeRole && (
        <RoleManageDialog
          role={activeRole}
          open={!!manageRole}
          onOpenChange={(open) => !open && setManageRole(null)}
        />
      )}
    </>
  )
}
