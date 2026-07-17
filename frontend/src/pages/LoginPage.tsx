import { useState, type FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { LayoutGrid, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/lib/auth-store'
import { authApi } from '@/lib/endpoints'
import { apiErrorMessage } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const setTokens = useAuthStore((s) => s.setTokens)
  const setUser = useAuthStore((s) => s.setUser)
  const navigate = useNavigate()
  const location = useLocation()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const tokens = await authApi.login(username, password)
      setTokens(tokens.access_token, tokens.refresh_token)
      const me = await authApi.me()
      setUser(me)
      const redirectTo = (location.state as { from?: Location })?.from?.pathname ?? '/users'
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(apiErrorMessage(err, 'Invalid username or password.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/40 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center text-center">
          <div className="mb-1 flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <LayoutGrid className="size-5" />
          </div>
          <CardTitle className="text-xl">Sign in</CardTitle>
          <CardDescription>Admin console access</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
            <Button type="submit" disabled={loading} className="mt-1 w-full">
              {loading && <Loader2 className="animate-spin" />}
              Sign in
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
