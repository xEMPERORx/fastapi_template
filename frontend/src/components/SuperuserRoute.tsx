import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '@/lib/auth-store'

// Client-side UX only, mirrors `superuser_required()` on the backend — the
// API re-checks on every request regardless, this just keeps a tenant user
// from landing on a page that would 403 on its first fetch.
export function SuperuserRoute() {
  const isSuperuser = useAuthStore((s) => s.user?.is_superuser)

  if (!isSuperuser) {
    return <Navigate to="/users" replace />
  }

  return <Outlet />
}
