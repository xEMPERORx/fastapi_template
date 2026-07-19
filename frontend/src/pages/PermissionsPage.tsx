import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search } from 'lucide-react'
import { permissionsApi } from '@/lib/endpoints'
import { PageHeader } from '@/components/PageHeader'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

export function PermissionsPage() {
  const [search, setSearch] = useState('')
  const { data: permissions, isLoading } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => permissionsApi.list(),
  })

  const filtered = useMemo(() => {
    if (!permissions) return []
    const q = search.trim().toLowerCase()
    if (!q) return permissions
    return permissions.filter((p) => p.name.toLowerCase().includes(q))
  }, [permissions, search])

  return (
    <>
      <PageHeader
        title="Permissions"
        description="The fixed catalog of actions roles can bundle, or that can be granted to a user directly. Defined in code, not editable here."
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
                <TableHead>Name</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading &&
                Array.from({ length: 6 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell>
                      <Skeleton className="h-9 w-full" />
                    </TableCell>
                  </TableRow>
                ))}

              {!isLoading && filtered.length === 0 && (
                <TableRow>
                  <TableCell className="py-8 text-center text-sm text-muted-foreground">
                    No permissions match your search.
                  </TableCell>
                </TableRow>
              )}

              {filtered.map((permission) => (
                <TableRow key={permission.id}>
                  <TableCell className="font-mono text-xs">{permission.name}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </>
  )
}
