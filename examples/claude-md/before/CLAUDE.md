# CLAUDE.md

Welcome! In this document we will walk through everything you need to know about working in the Lumen codebase. Please note that this file is read by Claude Code at the start of every session, so it is important to keep it up to date. Let's get started.

## About the project

Lumen is a small SaaS product for scheduling social media posts. Basically it is a Next.js 14 app (App Router) with a Postgres database behind Prisma, a background worker that publishes posts, and a Stripe integration for billing. The repository is a monorepo managed with pnpm workspaces.

As you can see, there are three packages:

- `apps/web` is the Next.js application that serves the dashboard and the marketing pages.
- `apps/worker` is the background worker that polls the queue and publishes posts.
- `packages/db` contains the Prisma schema, the generated client and the migrations.

It is worth noting that the three packages share one TypeScript config and one ESLint config from the repository root.

## Golden rules

- You MUST run `pnpm test` before every commit.
- You MUST NOT commit directly to `main`; open a pull request.
- NEVER edit files under `packages/db/migrations` by hand; generate them with `pnpm db:migrate`.
- ALWAYS use pnpm for installing packages.
- Never use npm or yarn in this repository.
- Do not add a dependency without saying why in the PR description.
- Keep in mind that the worker and the web app share the Prisma client, so a schema change touches both.
- Always use pnpm for installing packages.

## Coding conventions

We use TypeScript everywhere. It is important to keep the code strict, so `strict: true` is on and you should not add `// @ts-ignore` unless there is a comment explaining why.

- Prefer named exports over default exports.
- Use the `@/` alias for imports inside `apps/web`; do not use long relative paths like `../../../lib`.
- Components live in `apps/web/components`, one component per file, file name in kebab-case.
- Server actions go in `apps/web/actions` and must be marked with `"use server"`.
- Prefer named exports to default exports.
- Do not use `any`. If you really have to, use `unknown` and narrow it.
- Format with Prettier (the config is in the root). Do not fight the formatter.
- Always use tabs for indentation.

### Error handling

Obviously errors should be handled. Wrap external calls (Stripe, social APIs) in `try/catch` and convert failures into the `AppError` class from `apps/web/lib/errors.ts`. Never swallow an error silently: either rethrow, or log it with `logger.error` and return a typed failure.

Remember that route handlers must return `NextResponse.json({ error })` with the right status code, not throw.

## Testing

We use Vitest for unit tests and Playwright for end-to-end tests. In order to run them:

```bash
pnpm test          # unit tests, all packages
pnpm test:e2e      # Playwright, needs the dev server running
pnpm test -- --watch
```

Please make sure to run `pnpm test` before every commit. Tests live next to the code as `*.test.ts`. End-to-end tests live in `apps/web/e2e`.

Note that the e2e suite needs the seed data; run `pnpm db:seed` first if the suite complains about a missing workspace.

## Local setup

The following section describes how to set up a development environment from scratch. Feel free to skip it if you already have one.

First, you will need Node 20 and pnpm 9. We recommend that you install Node through a version manager. Then install Postgres 16 locally or run it in Docker. Below you will find the full procedure.

```bash
# 1. clone and install
git clone git@github.com:example/lumen.git
cd lumen
corepack enable
pnpm install

# 2. database
docker run --name lumen-pg -e POSTGRES_PASSWORD=lumen -p 5432:5432 -d postgres:16
cp .env.example .env
# edit DATABASE_URL in .env to point at the container

# 3. schema and seed data
pnpm db:migrate
pnpm db:seed

# 4. Stripe (optional for most work)
stripe login
stripe listen --forward-to localhost:3000/api/stripe/webhook
# copy the webhook signing secret into STRIPE_WEBHOOK_SECRET in .env

# 5. run everything
pnpm dev            # web on :3000, worker in the same terminal
pnpm dev --filter web
pnpm dev --filter worker

# 6. useful checks
pnpm lint
pnpm typecheck
pnpm db:studio      # Prisma Studio on :5555
```

Environment variables you will need (the names only; values are in your password manager):

| Variable | Used by | Notes |
|---|---|---|
| `DATABASE_URL` | web, worker | Postgres connection string |
| `NEXTAUTH_SECRET` | web | any random 32-byte string in development |
| `NEXTAUTH_URL` | web | `http://localhost:3000` in development |
| `STRIPE_SECRET_KEY` | web | test-mode key |
| `STRIPE_WEBHOOK_SECRET` | web | from `stripe listen` |
| `STRIPE_PRICE_PRO` | web | price id of the Pro plan |
| `TWITTER_CLIENT_ID` | web, worker | OAuth app |
| `TWITTER_CLIENT_SECRET` | web, worker | OAuth app |
| `LINKEDIN_CLIENT_ID` | web, worker | OAuth app |
| `LINKEDIN_CLIENT_SECRET` | web, worker | OAuth app |
| `QUEUE_POLL_MS` | worker | default 5000 |
| `LOG_LEVEL` | web, worker | `debug` locally |
| `SENTRY_DSN` | web, worker | optional locally |
| `RESEND_KEY` | web | transactional email, optional locally |

If `pnpm install` fails with a lockfile error, delete the lockfile and run it again. If Prisma complains about the engine, run `pnpm db:generate`. If the worker cannot reach Postgres, check that the Docker container is running with `docker ps`. If the e2e tests fail on a fresh machine, install the Playwright browsers with `pnpm exec playwright install`.

You should always restart the dev server after changing anything in `packages/db`, because the generated client is cached.

### Local setup

See above.

## API conventions

All HTTP endpoints live under `apps/web/app/api`. Here we describe the shape every endpoint follows so that the client code stays predictable.

- Every response is JSON. Successful responses return `{ data }`, failures return `{ error: { code, message } }`.
- Use the HTTP verbs properly: GET reads, POST creates, PATCH updates, DELETE deletes. Do not use POST for everything.
- Every endpoint validates its input with Zod before touching the database. Put the schema in the same file as the handler.
- Pagination is cursor based: accept `cursor` and `limit` (max 100), return `nextCursor`.
- Dates are ISO 8601 strings in UTC. Never return a Date object or a Unix timestamp.
- Auth: call `requireSession()` at the top of every handler. Endpoints without it are public, and public endpoints need a comment saying so.
- Rate limiting: public endpoints go through `withRateLimit` from `apps/web/lib/rate-limit.ts`.
- Versioning: there is none yet. Do not add `/v1/` prefixes.

Example of a compliant handler:

```ts
import { NextResponse } from "next/server";
import { z } from "zod";
import { requireSession } from "@/lib/auth";
import { db } from "@lumen/db";
import { AppError } from "@/lib/errors";

const Body = z.object({
  text: z.string().min(1).max(280),
  scheduledAt: z.string().datetime(),
  accountId: z.string().cuid(),
});

export async function POST(req: Request) {
  const session = await requireSession();
  const json = await req.json();
  const parsed = Body.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: { code: "invalid_body", message: parsed.error.message } }, { status: 400 });
  }
  try {
    const post = await db.post.create({
      data: { ...parsed.data, workspaceId: session.workspaceId },
    });
    return NextResponse.json({ data: post }, { status: 201 });
  } catch (e) {
    const err = AppError.from(e);
    return NextResponse.json({ error: { code: err.code, message: err.message } }, { status: err.status });
  }
}
```

## Git workflow

- Branch names: `feat/<short-name>`, `fix/<short-name>`, `chore/<short-name>`.
- Commit messages follow Conventional Commits.
- You MUST NOT commit directly to `main`; open a pull request.
- Squash-merge pull requests. Last but not least, delete the branch after merging.

## Deployment

## Things that are easy to get wrong

- The worker uses its own Prisma client instance; do not import the web app's.
- Never use tabs for indentation.
- Prettier is configured for two spaces; the formatter wins.
- `scheduledAt` is stored in UTC. Convert at the edge, in the UI, never in the database layer.
- Stripe webhooks arrive out of order. Handlers must be idempotent.
