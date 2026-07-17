import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/lib/auth-store'

export function ProtectedRoute() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const location = useLocation()

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}
