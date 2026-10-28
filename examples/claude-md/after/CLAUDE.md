# CLAUDE.md

Lumen: Next.js 14 (App Router) + Prisma/Postgres + a publish worker + Stripe. pnpm monorepo: `apps/web` (dashboard, marketing), `apps/worker` (queue poller), `packages/db` (schema, client, migrations). Root holds the shared tsconfig and ESLint config.

## Rules

- You MUST run `pnpm test` before every commit.
- You MUST NOT commit directly to `main`; open a pull request.
- NEVER edit files under `packages/db/migrations` by hand; generate them with `pnpm db:migrate`.
- ALWAYS use pnpm for installing packages.
- Never use npm or yarn in this repository.
- Do not add a dependency without saying why in the PR description.
- A schema change in `packages/db` touches web and worker; restart the dev server after it (the generated client is cached).

## Code

- TypeScript, `strict: true`. No `// @ts-ignore` without a comment saying why.
- Prefer named exports over default exports.
- Use the `@/` alias for imports inside `apps/web`; do not use long relative paths like `../../../lib`.
- Components: `apps/web/components`, one per file, kebab-case file names.
- Server actions go in `apps/web/actions` and must be marked with `"use server"`.
- Do not use `any`. If you really have to, use `unknown` and narrow it.
- Format with Prettier (the config is in the root). Do not fight the formatter.
- Never use tabs for indentation.
- Errors: wrap external calls (Stripe, social APIs) in `try/catch`, convert to `AppError` (`apps/web/lib/errors.ts`). Never swallow an error silently: either rethrow, or log it with `logger.error` and return a typed failure.
- Route handlers must return `NextResponse.json({ error })` with the right status code, not throw.

## API (`apps/web/app/api`)

- Responses are JSON: `{ data }` on success, `{ error: { code, message } }` on failure.
- Use the HTTP verbs properly: GET reads, POST creates, PATCH updates, DELETE deletes. Do not use POST for everything.
- Validate input with Zod in the handler file, before touching the database.
- Pagination is cursor based: accept `cursor` and `limit` (max 100), return `nextCursor`.
- Dates are ISO 8601 strings in UTC. Never return a Date object or a Unix timestamp.
- Auth: call `requireSession()` at the top of every handler. Endpoints without it are public, and public endpoints need a comment saying so.
- Public endpoints go through `withRateLimit` (`apps/web/lib/rate-limit.ts`).
- Versioning: there is none yet. Do not add `/v1/` prefixes.
- Full handler example: [references/api-conventions.md](references/api-conventions.md).

## Tests

Vitest (`pnpm test`, `*.test.ts` next to the code) and Playwright (`pnpm test:e2e`, `apps/web/e2e`, needs the dev server and `pnpm db:seed`).

## Git

Branches `feat/`, `fix/`, `chore/` + short name. Conventional Commits. Squash-merge, delete the branch after merging.

## Gotchas

- The worker uses its own Prisma client instance; do not import the web app's.
- `scheduledAt` is stored in UTC. Convert at the edge, in the UI, never in the database layer.
- Stripe webhooks arrive out of order. Handlers must be idempotent.

Setup from scratch, env var names, troubleshooting: [references/local-setup.md](references/local-setup.md).
