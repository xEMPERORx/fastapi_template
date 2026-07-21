import { useQuery } from '@tanstack/react-query'
import { permissionsApi } from '@/lib/endpoints'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'

// Superuser-only control: lets them pick which catalog permissions a tenant's
// roles may ever hold (see `Tenant.allowed_permission_mask`). Always fetches
// the full catalog — `permissionsApi.list()` only returns a caller's own
// effective permissions for a non-superuser, but every place this component
// is used is gated by `SuperuserRoute`.
export function PermissionCheckboxList({
  selected,
  onChange,
}: {
  selected: string[]
  onChange: (names: string[]) => void
}) {
  const { data: permissions, isLoading } = useQuery({
    queryKey: ['permissions', 'catalog'],
    queryFn: () => permissionsApi.list(0, 200),
  })

  function toggle(name: string, checked: boolean) {
    onChange(checked ? [...selected, name] : selected.filter((n) => n !== name))
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-5 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid max-h-56 grid-cols-1 gap-x-4 gap-y-2 overflow-y-auto rounded-md border p-3 sm:grid-cols-2">
      {(permissions ?? []).map((permission) => (
        <div key={permission.id} className="flex items-center gap-2">
          <Checkbox
            id={`perm-${permission.id}`}
            checked={selected.includes(permission.name)}
            onCheckedChange={(checked) => toggle(permission.name, checked === true)}
          />
          <Label htmlFor={`perm-${permission.id}`} className="font-mono text-xs font-normal">
            {permission.name}
          </Label>
        </div>
      ))}
    </div>
  )
}
