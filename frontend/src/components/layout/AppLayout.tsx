import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutGrid, LayoutDashboard, Users, ShieldCheck, KeyRound, LogOut, Building2, Menu } from 'lucide-react'
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
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'

const SUPERUSER_NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/tenants', label: 'Tenants', icon: Building2, end: false },
]

const TENANT_NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/users', label: 'Users', icon: Users, end: false },
  { to: '/roles', label: 'Roles', icon: ShieldCheck, end: false },
  { to: '/permissions', label: 'Permissions', icon: KeyRound, end: false },
]

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const user = useAuthStore((s) => s.user)
  const clear = useAuthStore((s) => s.clear)
  const navigate = useNavigate()
  const navItems = user?.is_superuser ? SUPERUSER_NAV_ITEMS : TENANT_NAV_ITEMS

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
    <div className="flex h-full flex-col">
      <div className="flex h-14 items-center gap-2 px-4">
        <LayoutGrid className="size-5 text-sidebar-primary" />
        <div className="flex min-w-0 flex-col leading-tight">
          <span className="truncate text-sm font-semibold tracking-tight">
            {user?.is_superuser ? 'Admin' : (user?.tenant_name ?? 'Admin')}
          </span>
          {user?.is_superuser && (
            <span className="text-[11px] text-sidebar-foreground/60">All tenants</span>
          )}
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-2 py-2">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors duration-150 ${
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
          <DropdownMenuTrigger className="flex w-full items-center gap-2.5 rounded-md px-2 py-2 text-left text-sm transition-colors duration-150 hover:bg-sidebar-accent">
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
    </div>
  )
}

export function AppLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className="flex min-h-svh w-full">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground md:flex">
        <SidebarContent />
      </aside>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-72 border-sidebar-border bg-sidebar p-0 text-sidebar-foreground">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarContent onNavigate={() => setMobileNavOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex h-14 shrink-0 items-center gap-2 border-b border-border px-4 md:hidden">
          <Button variant="ghost" size="icon-sm" onClick={() => setMobileNavOpen(true)}>
            <Menu />
            <span className="sr-only">Open navigation</span>
          </Button>
          <div className="flex items-center gap-2">
            <LayoutGrid className="size-4 text-primary" />
            <span className="text-sm font-semibold tracking-tight">Admin</span>
          </div>
        </div>

        <main className="flex min-w-0 flex-1 flex-col overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
