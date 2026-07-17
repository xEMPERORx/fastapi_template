import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Search, ShieldAlert } from 'lucide-react'
import { usersApi } from '@/lib/endpoints'
import { PageHeader } from '@/components/PageHeader'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

const PAGE_SIZE = 20

export function UsersListPage() {
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')

  const { data: users, isLoading, isError } = useQuery({
    queryKey: ['users', page],
    queryFn: () => usersApi.list(page * PAGE_SIZE, PAGE_SIZE),
  })

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
      <PageHeader title="Users" description="View accounts, roles, and direct permission grants." />

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
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={3}>
                      <Skeleton className="h-9 w-full" />
                    </TableCell>
                  </TableRow>
                ))}

              {isError && (
                <TableRow>
                  <TableCell colSpan={3} className="py-8 text-center text-sm text-muted-foreground">
                    Couldn't load users.
                  </TableCell>
                </TableRow>
              )}

              {!isLoading && !isError && filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="py-8 text-center text-sm text-muted-foreground">
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
                    <Badge variant={user.is_verified ? 'default' : 'outline'}>
                      {user.is_verified ? 'Verified' : 'Unverified'}
                    </Badge>
                  </TableCell>
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
