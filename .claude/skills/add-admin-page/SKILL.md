---
name: add-admin-page
description: >
  Guide for adding a new page to the admin frontend (frontend/) in this FastAPI
  template. Use when user asks to "add an admin page", "add a screen to the
  dashboard", "add a frontend route", or extends the users/roles/permissions UI.
---

The admin SPA lives in `frontend/` — Vite + React + TypeScript + Tailwind + shadcn/ui
(Base UI primitives, Nova preset). It's built with `npm run build` and served by the
backend itself via `app.frontend()` in `app/main.py` — there is no separate frontend
server in production, and no proxy config to maintain beyond `vite.config.ts`'s dev-only
`/api` proxy to `localhost:8000`.

## Conventions

- **API calls**: never call `fetch`/`axios` directly from a page. Add typed functions
  to `src/lib/endpoints.ts`, grouped by backend domain (`usersApi`, `rolesApi`, ...).
  They all go through the shared `src/lib/api.ts` axios instance, which already
  attaches the bearer token and retries once through `/auth/refresh` on a 401.
- **Types**: add response/request shapes to `src/lib/types.ts`, mirroring the backend
  Pydantic schema field-for-field (see `app/schema/`). Keep names matching the backend
  JSON keys (snake_case) rather than converting to camelCase — less to keep in sync.
- **Data fetching**: `@tanstack/react-query` (`useQuery`/`useMutation`), not raw
  `useEffect` + `useState`. Invalidate the relevant query key(s) in a mutation's
  `onSuccess`. Use `toast.success`/`toast.error` (from `sonner`, already wired via
  `<Toaster />` in `main.tsx`) for mutation feedback — `apiErrorMessage(err)` from
  `src/lib/api.ts` extracts the backend's `message` field for the toast text.
- **Auth guarding**: routes needing a logged-in user go under the `<ProtectedRoute />`
  element in `App.tsx` (redirects to `/login` if no access token). Routes needing a
  specific permission should hide/disable the relevant action client-side using
  `usersApi.myGrants()` — but this is only a UX nicety; **the backend re-checks on
  every mutating call regardless**, so never skip that check assuming the frontend
  filtered correctly.
- **Layout**: pages needing the sidebar/nav go under the `<AppLayout />` route in
  `App.tsx` and render inside its `<Outlet />`. Use the shared `<PageHeader>` component
  for the title/description/actions row at the top of a page.
- **Components**: use what's already in `src/components/ui/` (shadcn) before adding a
  new dependency. These are Base UI under the hood, not Radix — triggers use a
  `render={<Button />}` prop instead of an `asChild` prop, and `Select`'s
  `onValueChange` receives `string | null` (wrap state setters:
  `(value) => setX(value ?? '')`).
- **Design register**: this is a product/dashboard surface (design serves the task, not
  brand). Restrained color (one accent, used for primary actions/current
  selection/state only — see `--primary`/`--ring` in `src/index.css`), one type family
  (Geist), skeleton loading states over spinners, standard nav patterns. Load the
  `impeccable` skill's `product.md` register before styling a new page from scratch.

## Adding a new page — steps

1. Add any new API functions to `src/lib/endpoints.ts` and types to `src/lib/types.ts`.
2. Create `src/pages/YourPage.tsx`. Start from `RolesPage.tsx` or `PermissionsPage.tsx`
   as a template if the page is a list + create/delete pattern; `UserDetailPage.tsx` if
   it's a detail view with grant/revoke actions.
3. Register the route in `App.tsx`, under `<ProtectedRoute>` / `<AppLayout>` as needed.
4. If it belongs in primary navigation, add it to `NAV_ITEMS` in
   `src/components/layout/AppLayout.tsx`.
5. `npm run build` in `frontend/` and confirm it's served — start the backend
   (`uvicorn app.main:app`) and hit `/` and your new route path directly (the SPA
   fallback handles client-side routing; only real 404s are missing static assets).

## What NOT to do

- Don't persist the access or refresh token to `localStorage` — they're deliberately
  in-memory only (`src/lib/auth-store.ts`) to limit XSS exposure. A hard reload
  returning to `/login` is the intended tradeoff, not a bug to "fix" by persisting.
- Don't hardcode `http://localhost:8000` anywhere — API calls are relative
  (`/api/v1/...`) so the same build works in dev (via the Vite proxy) and production
  (served from the same origin by FastAPI).
- Don't build a new modal/dialog pattern when `Dialog` from `components/ui` covers it.
- Don't skip the backend permission check because "the button is already hidden" — see
  the auth-guarding note above.
