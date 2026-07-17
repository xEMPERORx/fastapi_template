import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutGrid, Users, ShieldCheck, KeyRound, LogOut } from 'lucide-react'
import { useAuthStore } from '@/lib/auth-store'
import { authApi } from '@/lib/endpoints'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

const NAV_ITEMS = [
  { to: '/users', label: 'Users', icon: Users },
  { to: '/roles', label: 'Roles', icon: ShieldCheck },
  { to: '/permissions', label: 'Permissions', icon: KeyRound },
]

export function AppLayout() {
  const user = useAuthStore((s) => s.user)
  const clear = useAuthStore((s) => s.clear)
  const navigate = useNavigate()

  async function handleLogout() {
    try {
      await authApi.logout()
    } catch {
      // best effort — clear local state regardless
    }
    clear()
    navigate('/login', { replace: true })
  }

  const initials = (user?.username ?? '?').slice(0, 2).toUpperCase()

  return (
    <div className="flex min-h-svh w-full">
      <aside className="flex w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
        <div className="flex h-14 items-center gap-2 px-4">
          <LayoutGrid className="size-5 text-sidebar-primary" />
          <span className="text-sm font-semibold tracking-tight">Admin</span>
        </div>

        <nav className="flex flex-1 flex-col gap-0.5 px-2 py-2">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                    : 'text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'
                }`
              }
            >
              <Icon className="size-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-sidebar-border p-2">
          <DropdownMenu>
            <DropdownMenuTrigger className="flex w-full items-center gap-2.5 rounded-md px-2 py-2 text-left text-sm hover:bg-sidebar-accent">
              <Avatar className="size-7">
                <AvatarFallback className="text-xs">{initials}</AvatarFallback>
              </Avatar>
              <div className="flex min-w-0 flex-col">
                <span className="truncate font-medium">{user?.username}</span>
                <span className="truncate text-xs text-sidebar-foreground/60">{user?.email}</span>
              </div>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" side="top" className="w-56">
              <DropdownMenuLabel>Signed in as {user?.username}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} variant="destructive">
                <LogOut />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
