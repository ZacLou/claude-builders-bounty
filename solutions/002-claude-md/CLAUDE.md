# CLAUDE.md — Next.js 15 + SQLite SaaS

Use this file as the single source of truth for every Claude Code interaction in this project. If a rule below conflicts with a generic recommendation, this file wins.

## 1. Stack & versions

- **Framework:** Next.js 15 (App Router), React 19, TypeScript 5.
- **Styling:** Tailwind CSS 3.4 + shadcn/ui primitives. No inline `style` props except for dynamic values computed in JS.
- **Database:** SQLite via `better-sqlite3` for local/self-hosted, or Turso (`@libsql/client`) for cloud. Default to `better-sqlite3` unless `TURSO_DATABASE_URL` is set.
- **ORM:** None. Use handwritten SQL in `src/lib/db.ts` with strict parameter binding.
- **Auth:** Lucia v3 + OAuth providers (GitHub/Google). No JWT secrets checked into git.
- **Validation:** Zod for all forms, API bodies, and query params.
- **Testing:** Vitest for unit, Playwright for critical e2e flows.

## 2. Folder structure

```
src/
  app/              # Next.js App Router routes, layouts, loading.tsx, error.tsx
  components/       # React components; co-locate `.test.tsx` when useful
  lib/              # Pure utilities, DB helpers, auth
  db/               # Migrations (.sql) and seed scripts
  types/            # Shared TypeScript types ONLY; no runtime code
```

Rules:
- Keep route handlers (`route.ts`) thin: validate input, call a lib function, return response.
- Business logic lives in `src/lib/`, never in `app/` route files or components.
- One component per file unless the sub-components are tiny and purely presentational.

## 3. Database conventions

- Migrations are immutable files in `src/db/migrations/YYYYMMDDHHMMSS_description.sql`.
- Run migrations with `npm run db:migrate`. Never edit a migration that has been committed.
- Table names are plural snake_case (`users`, `organizations`, `subscription_plans`).
- Primary keys are `INTEGER PRIMARY KEY AUTOINCREMENT` (or Turso `TEXT` UUID when multi-region).
- Foreign keys must have `ON DELETE CASCADE` unless business rules require restrict.
- Store timestamps as Unix seconds (`INTEGER NOT NULL`), not strings.
- Every query uses parameter binding. String interpolation in SQL is forbidden.

## 4. Component patterns

- Use Server Components by default. Mark `"use client"` only when you need hooks, browser APIs, or event handlers.
- Fetch data in Server Components via `src/lib/db.ts` helpers, not `useEffect` + fetch.
- Forms use `react-hook-form` + Zod resolvers. Client-side validation mirrors server validation.
- Loading states: prefer `loading.tsx` skeletons over inline spinners.
- Error boundaries: every route segment that does DB/IO must have `error.tsx`.

## 5. API conventions

- All API routes live under `src/app/api/` and return typed JSON.
- Validate with Zod before touching the database.
- Return `{ success: true, data: ... }` or `{ success: false, error: ... }` consistently.
- HTTP status codes: 200 success, 400 validation, 401 unauthorized, 404 not found, 500 unexpected.

## 6. What we DON'T do

- No `any`. If you cannot type it, ask before proceeding.
- No ORM migrations generated from model definitions. Migrations are hand-written SQL.
- No CSS-in-JS (styled-components, emotion). Tailwind only.
- No client-side data fetching for initial page data. Use Server Components.
- No monolithic `utils.ts`. Split helpers by domain (`src/lib/date.ts`, `src/lib/currency.ts`, etc.).
- No secrets in `.env.example` placeholders. Commit only keys, never values.

## 7. Environment variables

Required keys (add real values in `.env.local`):

```env
DATABASE_URL="file:./data.sqlite"
# OR
TURSO_DATABASE_URL=""
TURSO_AUTH_TOKEN=""

GITHUB_CLIENT_ID=""
GITHUB_CLIENT_SECRET=""

NEXT_PUBLIC_APP_URL="http://localhost:3000"
```

## 8. Common commands

```bash
npm run dev          # start Next.js dev server
npm run db:migrate   # apply migrations
npm run db:seed      # seed local dev data
npm run test         # vitest
npm run test:e2e     # playwright
npm run lint         # eslint + prettier --check
npm run format       # prettier --write
```

## 9. Testing rule

- Every DB helper in `src/lib/` must have at least one unit test against an in-memory SQLite DB.
- Playwright covers: sign-in flow, create-resource flow, delete-resource flow.

## 10. Reasoning summary

This stack is chosen to keep the codebase small, fast, and deployable anywhere:
- SQLite removes infrastructure overhead for early-stage SaaS.
- Hand-written SQL keeps query behavior explicit and reviewable.
- Server Components reduce client JS and simplify data loading.
- Strong typing + Zod prevents an entire class of runtime errors at the boundary.
