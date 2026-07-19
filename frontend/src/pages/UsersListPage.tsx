import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import { Ban, CheckCircle2, ChevronLeft, ChevronRight, Plus, Search, ShieldAlert } from 'lucide-react'
import { toast } from 'sonner'
import { usersApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import { PageHeader } from '@/components/PageHeader'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
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

const PAGE_SIZE = 20
const emptyForm = { username: '', email: '', password: '' }

export function UsersListPage() {
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: users, isLoading, isError } = useQuery({
    queryKey: ['users', page],
    queryFn: () => usersApi.list(page * PAGE_SIZE, PAGE_SIZE),
  })

  const grantsQuery = useQuery({
    queryKey: ['users', 'me', 'grants'],
    queryFn: () => usersApi.myGrants(),
  })
  const canCreateUser = grantsQuery.data?.effective_permissions.includes('user:create') ?? false
  const canDeactivateUser = grantsQuery.data?.effective_permissions.includes('user:deactivate') ?? false

  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState(emptyForm)

  const createUser = useMutation({
    mutationFn: () => usersApi.create(form.username, form.email, form.password),
    onSuccess: (user) => {
      toast.success(`User "${user.username}" created`)
      setForm(emptyForm)
      setCreateOpen(false)
      queryClient.invalidateQueries({ queryKey: ['users'] })
      navigate(`/users/${user.id}`)
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not create user')),
  })

  const setActive = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) =>
      active ? usersApi.activate(id) : usersApi.deactivate(id),
    onSuccess: (_data, { active }) => {
      toast.success(active ? 'User activated' : 'User deactivated')
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (err) => toast.error(apiErrorMessage(err, 'Could not update user')),
  })

  function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (form.username.trim() && form.email.trim() && form.password) createUser.mutate()
  }

  const filtered = useMemo(() => {
    if (!users) return []
    const q = search.trim().toLowerCase()
    if (!q) return users
    return users.filter(
      (u) => u.username.toLowerCase().includes(q) || u.email.toLowerCase().includes(q),
    )
  }, [users, search])

  return (
    <>
      <PageHeader
        title="Users"
        description="View users, roles, and direct permission grants."
        actions={
          canCreateUser ? (
            <Dialog
              open={createOpen}
              onOpenChange={(open) => { setCreateOpen(open); if (!open) setForm(emptyForm) }}
            >
              <DialogTrigger render={<Button size="sm" />}>
                <Plus />
                New user
              </DialogTrigger>
              <DialogContent className="sm:max-w-sm">
                <form onSubmit={handleCreate}>
                  <DialogHeader>
                    <DialogTitle>New user</DialogTitle>
                    <DialogDescription>
                      Added to your own organization. You can assign roles and permissions
                      right after creating them.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="flex flex-col gap-4 py-4">
                    <div className="flex flex-col gap-1.5">
                      <Label htmlFor="new-user-username">Username</Label>
                      <Input
                        id="new-user-username"
                        autoFocus
                        value={form.username}
                        onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                        required
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <Label htmlFor="new-user-email">Email</Label>
                      <Input
                        id="new-user-email"
                        type="email"
                        value={form.email}
                        onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                        required
                      />
                    </div>
                    <div className="flex flex-col gap-1.5">
                      <Label htmlFor="new-user-password">Password</Label>
                      <Input
                        id="new-user-password"
                        type="password"
                        value={form.password}
                        onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                        required
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button
                      type="submit"
                      disabled={
                        createUser.isPending || !form.username.trim() || !form.email.trim() || !form.password
                      }
                    >
                      Create user
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          ) : undefined
        }
      />

      <div className="flex flex-col gap-4 p-6">
        <div className="relative max-w-xs">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search this page..."
            className="pl-8"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Roles</TableHead>
                <TableHead>Status</TableHead>
                {canDeactivateUser && <TableHead className="w-16" />}
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={4}>
                      <Skeleton className="h-9 w-full" />
                    </TableCell>
                  </TableRow>
                ))}

              {isError && (
                <TableRow>
                  <TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">
                    Couldn't load users.
                  </TableCell>
                </TableRow>
              )}

              {!isLoading && !isError && filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">
                    No users match your search.
                  </TableCell>
                </TableRow>
              )}

              {filtered.map((user) => (
                <TableRow key={user.id}>
                  <TableCell>
                    <Link to={`/users/${user.id}`} className="block">
                      <div className="font-medium text-foreground hover:underline">
                        {user.username}
                      </div>
                      <div className="text-xs text-muted-foreground">{user.email}</div>
                    </Link>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {user.is_superuser && (
                        <Badge variant="secondary" className="gap-1">
                          <ShieldAlert className="size-3" />
                          superuser
                        </Badge>
                      )}
                      {user.roles.length === 0 && !user.is_superuser && (
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
                    </div>
                  </TableCell>
                  {canDeactivateUser && (
                    <TableCell>
                      {!user.is_superuser && (
                        <div className="flex justify-end">
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            disabled={setActive.isPending}
                            onClick={() => setActive.mutate({ id: user.id, active: !user.is_active })}
                          >
                            {user.is_active ? <Ban /> : <CheckCircle2 />}
                            <span className="sr-only">
                              {user.is_active ? `Deactivate ${user.username}` : `Activate ${user.username}`}
                            </span>
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">Page {page + 1}</p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page === 0}
              onClick={() => setPage((p) => Math.max(0, p - 1))}
            >
              <ChevronLeft />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!users || users.length < PAGE_SIZE}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
              <ChevronRight />
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
