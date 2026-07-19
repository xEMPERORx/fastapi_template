import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { SuperuserRoute } from '@/components/SuperuserRoute'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { UsersListPage } from '@/pages/UsersListPage'
import { UserDetailPage } from '@/pages/UserDetailPage'
import { RolesPage } from '@/pages/RolesPage'
import { PermissionsPage } from '@/pages/PermissionsPage'
import { TenantsPage } from '@/pages/TenantsPage'
import { TenantDetailPage } from '@/pages/TenantDetailPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="/users" element={<UsersListPage />} />
          <Route path="/users/:userId" element={<UserDetailPage />} />
          <Route path="/roles" element={<RolesPage />} />
          <Route path="/permissions" element={<PermissionsPage />} />
          <Route element={<SuperuserRoute />}>
            <Route path="/tenants" element={<TenantsPage />} />
            <Route path="/tenants/:tenantId" element={<TenantDetailPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
