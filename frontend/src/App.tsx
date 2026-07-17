import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { LoginPage } from '@/pages/LoginPage'
import { UsersListPage } from '@/pages/UsersListPage'
import { UserDetailPage } from '@/pages/UserDetailPage'
import { RolesPage } from '@/pages/RolesPage'
import { PermissionsPage } from '@/pages/PermissionsPage'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/users" replace />} />
          <Route path="/users" element={<UsersListPage />} />
          <Route path="/users/:userId" element={<UserDetailPage />} />
          <Route path="/roles" element={<RolesPage />} />
          <Route path="/permissions" element={<PermissionsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
