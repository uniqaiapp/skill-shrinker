# Local setup

Read this only when setting up a machine or debugging the environment.

Requirements: Node 20, pnpm 9 (via corepack), Postgres 16 (local or Docker).

```bash
git clone git@github.com:example/lumen.git && cd lumen
corepack enable && pnpm install
docker run --name lumen-pg -e POSTGRES_PASSWORD=lumen -p 5432:5432 -d postgres:16
cp .env.example .env            # set DATABASE_URL to the container
pnpm db:migrate && pnpm db:seed
pnpm dev                        # web on :3000, worker in the same terminal
```

Stripe (optional): `stripe login`, then `stripe listen --forward-to localhost:3000/api/stripe/webhook` and copy the signing secret into `STRIPE_WEBHOOK_SECRET`.

Other commands: `pnpm dev --filter web|worker`, `pnpm lint`, `pnpm typecheck`, `pnpm db:studio` (:5555).

## Environment variables (names only)

| Variable | Used by | Notes |
|---|---|---|
| `DATABASE_URL` | web, worker | Postgres connection string |
| `NEXTAUTH_SECRET` | web | any random 32-byte string in development |
| `NEXTAUTH_URL` | web | `http://localhost:3000` in development |
| `STRIPE_SECRET_KEY` | web | test-mode key |
| `STRIPE_WEBHOOK_SECRET` | web | from `stripe listen` |
| `STRIPE_PRICE_PRO` | web | price id of the Pro plan |
| `TWITTER_CLIENT_ID` / `TWITTER_CLIENT_SECRET` | web, worker | OAuth app |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | web, worker | OAuth app |
| `QUEUE_POLL_MS` | worker | default 5000 |
| `LOG_LEVEL` | web, worker | `debug` locally |
| `SENTRY_DSN` | web, worker | optional locally |
| `RESEND_KEY` | web | transactional email, optional locally |

## Troubleshooting

- `pnpm install` lockfile error: delete the lockfile, run again.
- Prisma engine error: `pnpm db:generate`.
- Worker cannot reach Postgres: `docker ps`, check the container is up.
- e2e fails on a fresh machine: `pnpm exec playwright install`.
- You should always restart the dev server after changing anything in `packages/db`, because the generated client is cached.
