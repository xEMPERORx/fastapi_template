import { create } from 'zustand'
import type { UserResponse } from './types'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: UserResponse | null
  setTokens: (accessToken: string, refreshToken: string) => void
  setUser: (user: UserResponse | null) => void
  clear: () => void
}

// Access + refresh tokens live in memory only (not localStorage) to limit
// XSS blast radius. The backend's /auth/refresh endpoint takes the refresh
// token as a request body field rather than reading its httpOnly cookie, so
// there is no way to silently restore a session after a hard reload — that
// is a deliberate tradeoff, not an oversight. A reload always returns to the
// login page.
export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
  setUser: (user) => set({ user }),
  clear: () => set({ accessToken: null, refreshToken: null, user: null }),
}))
