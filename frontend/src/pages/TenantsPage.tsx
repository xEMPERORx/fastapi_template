import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Ban, CheckCircle2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { tenantsApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import { PageHeader } from '@/components/PageHeader'
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

const emptyForm = { name: '', adminUsername: '', adminEmail: '', adminPassword: '' }

export function TenantsPage() {
  const queryClient = useQueryClient()
  const { data: tenants, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => tenantsApi.list(),
  })

  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const createTenant = useMutation({
    mutationFn: () =>
      tenantsApi.create(form.name, form.adminUsername, form.adminEmail, form.adminPassword),
    onSuccess: (result) => {
      toast.success(`Tenant "${result.tenant.name}" created`, {
        description: `Admin account: ${result.admin.username} (${result.admin.email})`,
      })
      setForm(emptyForm)
      setCreateOpen(false)
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not create tenant')),
  })

  const setActive = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      active ? tenantsApi.activate(id) : tenantsApi.deactivate(id),
    onSuccess: (_data, { active }) => {
      toast.success(active ? 'Tenant activated' : 'Tenant deactivated')
      queryClient.invalidateQueries({ queryKey: ['tenants'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not update tenant')),
  })

  function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (form.name.trim() && form.adminUsername.trim() && form.adminEmail.trim() && form.adminPassword) {
      createTenant.mutate()
    }
  }

  const formValid =
    form.name.trim() && form.adminUsername.trim() && form.adminEmail.trim() && form.adminPassword

  return (
    <>
      <PageHeader
        title="Tenants"
        description="Every organization on this deployment. Creating a tenant also creates its first admin account."
        actions={
          <Dialog open={createOpen} onOpenChange={(open) => { setCreateOpen(open); if (!open) setForm(emptyForm) }}>
            <DialogTrigger render={<Button size="sm" />}>
              <Plus />
              New tenant
            </DialogTrigger>
            <DialogContent className="sm:max-w-sm">
              <form onSubmit={handleCreate}>
                <DialogHeader>
                  <DialogTitle>New tenant</DialogTitle>
                  <DialogDescription>
                    This also creates the tenant's first admin — they'll hold every
                    permission within their tenant and can create roles/users from there.
                  </DialogDescription>
                </DialogHeader>
                <div className="flex flex-col gap-4 py-4">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="tenant-name">Tenant name</Label>
                    <Input
                      id="tenant-name"
                      autoFocus
                      value={form.name}
                      onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                      placeholder="e.g. acme-industries"
                      required
                    />
                    <p className="text-xs text-muted-foreground">
                      Letters, numbers, and . _ - : only — no spaces.
                    </p>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="admin-username">Admin username</Label>
                    <Input
                      id="admin-username"
                      value={form.adminUsername}
                      onChange={(e) => setForm((f) => ({ ...f, adminUsername: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="admin-email">Admin email</Label>
                    <Input
                      id="admin-email"
                      type="email"
                      value={form.adminEmail}
                      onChange={(e) => setForm((f) => ({ ...f, adminEmail: e.target.value }))}
                      required
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="admin-password">Admin password</Label>
                    <Input
                      id="admin-password"
                      type="password"
                      value={form.adminPassword}
                      onChange={(e) => setForm((f) => ({ ...f, adminPassword: e.target.value }))}
                      required
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={createTenant.isPending || !formValid}>
                    Create tenant
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
                <TableHead>Tenant</TableHead>
                <TableHead>Status</TableHead>
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

              {!isLoading && tenants?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="py-8 text-center text-sm text-muted-foreground">
                    No tenants yet.
                  </TableCell>
                </TableRow>
              )}

              {tenants?.map((tenant) => (
                <TableRow key={tenant.id}>
                  <TableCell>
                    <Link to={`/tenants/${tenant.id}`} className="font-medium text-foreground hover:underline">
                      {tenant.name}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={tenant.is_active ? 'default' : 'outline'}>
                      {tenant.is_active ? 'Active' : 'Deactivated'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        disabled={setActive.isPending}
                        onClick={() => setActive.mutate({ id: tenant.id, active: !tenant.is_active })}
                      >
                        {tenant.is_active ? <Ban /> : <CheckCircle2 />}
                        <span className="sr-only">
                          {tenant.is_active ? `Deactivate ${tenant.name}` : `Activate ${tenant.name}`}
                        </span>
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
