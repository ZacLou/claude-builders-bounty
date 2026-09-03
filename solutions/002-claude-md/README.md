# CLAUDE.md for Next.js 15 + SQLite SaaS

This is an opinionated, production-ready `CLAUDE.md` for greenfield Next.js 15 App Router projects using SQLite (better-sqlite3 or Turso).

## How to use

1. Copy `CLAUDE.md` into the root of your Next.js project.
2. Open Claude Code in that project.
3. Claude will automatically load the context and follow the conventions defined here.

## What makes it opinionated

- **No ORM.** Hand-written SQL with parameter binding.
- **Server Components by default.** Fetch data server-side, keep client JS small.
- **Zod everywhere.** Forms, API bodies, and query params are validated.
- **Immutable migrations.** Never edit a committed migration file.
- **Tailwind only.** No CSS-in-JS.

## Tested

This CLAUDE.md was validated by creating a fresh Next.js 15 project and confirming Claude Code could scaffold routes, migrations, and components without asking clarifying questions.
