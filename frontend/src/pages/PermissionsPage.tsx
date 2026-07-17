import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { permissionsApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import { PageHeader } from '@/components/PageHeader'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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

export function PermissionsPage() {
  const queryClient = useQueryClient()
  const { data: permissions, isLoading } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => permissionsApi.list(),
  })

  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState('')

  const createPermission = useMutation({
    mutationFn: (name: string) => permissionsApi.create(name),
    onSuccess: () => {
      toast.success('Permission created')
      setNewName('')
      setCreateOpen(false)
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not create permission')),
  })

  const deletePermission = useMutation({
    mutationFn: (permissionId: number) => permissionsApi.remove(permissionId),
    onSuccess: () => {
      toast.success('Permission deleted')
      queryClient.invalidateQueries({ queryKey: ['permissions'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not delete permission')),
  })

  function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (newName.trim()) createPermission.mutate(newName.trim())
  }

  return (
    <>
      <PageHeader
        title="Permissions"
        description="Fine-grained actions that roles bundle, or that can be granted to a user directly."
        actions={
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogTrigger render={<Button size="sm" />}>
              <Plus />
              New permission
            </DialogTrigger>
            <DialogContent className="sm:max-w-sm">
              <form onSubmit={handleCreate}>
                <DialogHeader>
                  <DialogTitle>New permission</DialogTitle>
                  <DialogDescription>
                    Use a scoped name like <code className="text-xs">reports:export</code>.
                  </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-1.5 py-4">
                  <Label htmlFor="permission-name">Name</Label>
                  <Input
                    id="permission-name"
                    autoFocus
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. reports:export"
                    required
                  />
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={createPermission.isPending || !newName.trim()}>
                    Create permission
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
                <TableHead>Name</TableHead>
                <TableHead className="w-16" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                Array.from({ length: 4 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={2}>
                      <Skeleton className="h-9 w-full" />
                    </TableCell>
                  </TableRow>
                ))}

              {!isLoading && permissions?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={2} className="py-8 text-center text-sm text-muted-foreground">
                    No permissions yet.
                  </TableCell>
                </TableRow>
              )}

              {permissions?.map((permission) => (
                <TableRow key={permission.id}>
                  <TableCell className="font-mono text-xs">{permission.name}</TableCell>
                  <TableCell>
                    <div className="flex justify-end">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        disabled={deletePermission.isPending}
                        onClick={() => {
                          if (confirm(`Delete permission "${permission.name}"?`)) {
                            deletePermission.mutate(permission.id)
                          }
                        }}
                      >
                        <Trash2 />
                        <span className="sr-only">Delete {permission.name}</span>
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </>
  )
}
