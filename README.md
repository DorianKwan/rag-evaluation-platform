# RAG Observability and Evaluation Platform

A platform for running automated evaluation pipelines against RAG (Retrieval-Augmented Generation) systems. Define datasets of test cases, trigger evaluation runs, and track per-test-case scores across metrics like faithfulness, answer relevancy, context precision, and context recall — powered by [RAGAS](https://docs.ragas.io).

## Architecture

```
apps/
  web/dashboard/      React SPA (Vite) — dataset management and run monitoring
  service/core/       Hono API + BullMQ worker — orchestrates evaluation jobs
  service/eval/       Python FastAPI + RAGAS — stateless scorer, one job per test case
libs/
  config/             Shared tsconfig + eslint
  contracts/          /evaluate request/response schema (Zod + Pydantic, kept in sync)
  db/                 Prisma schema + generated client (sole owner)
```

**Data flow:** Dashboard → Core API → BullMQ queue → Core worker → Eval service → Core worker settles result → DB → webhook (optional).

The dashboard uses a typed [Hono RPC](https://hono.dev/docs/guides/rpc) client (`hc`) via a type-only import from `@/core/app-type`. The TS ↔ Python boundary is the `/evaluate` HTTP contract in `libs/contracts`. No other cross-service coupling exists.

## Services

### `@/core` — Core service (`apps/service/core`)

Two entrypoints, one package:

- **`app.ts`** — Hono HTTP API. Routes: create dataset, add test cases, trigger eval run, poll run status and results.
- **`worker.ts`** — BullMQ worker. Dequeues jobs, POSTs to eval, settles results via a `FOR UPDATE` transaction.

Both entrypoints import down into `src/shared/` (Prisma client, queue definitions, run-completion logic). Neither imports the other.

### `@/eval` — Eval service (`apps/service/eval`)

Python FastAPI + RAGAS. Stateless — no DB access. Accepts `POST /evaluate`, scores one test case, returns metric scores. Errors are HTTP error responses; core maps them to the `error` outcome.

### `@/dashboard` — Dashboard (`apps/web/dashboard`)

React SPA. Define datasets, trigger runs, watch test-case results settle in real time.

## Supported Metrics

| Metric | What it measures |
|---|---|
| `faithfulness` | Are claims in the response grounded in the retrieved context? |
| `answer_relevancy` | Does the response actually answer the question? |
| `context_precision` | Are the retrieved chunks relevant to the question? |
| `context_recall` | Did retrieval surface all necessary information? |

All scores are `[0, 1]`. Pass/fail per test case is determined by a configurable `passThreshold` (default `0.7`) snapshotted at run creation.

## Data Model

```
Dataset 1──* TestCase          # the source data
EvalRun  1──* EvalTestCase     # a snapshot of the dataset at run time
```

`EvalTestCase` snapshots `user_input` and `reference` from the dataset at run creation, so historical runs are unaffected by later dataset edits. Run completion is determined by a `FOR UPDATE` transaction that recounts settled test cases on every settle — no `settled_count` column.

Run status values: `pending → running → success | failed | error`.

## Local Dev

**Prerequisites:** Node ≥ 20, pnpm ≥ 9, Docker, Python ≥ 3.11, [uv](https://docs.astral.sh/uv/)

```bash
cp .env.example .env
docker compose up -d          # Postgres (5432) + Redis (6379)
pnpm install
pnpm turbo run build          # should no-op on stubs
```

Run the TypeScript services:

```bash
pnpm dev                      # starts all TS packages via Turborepo
```

Run the Python eval service (not managed by Turborepo):

```bash
cd apps/service/eval
uv run fastapi dev            # http://localhost:8000
```

### Database

```bash
pnpm --filter @/db db:migrate   # apply migrations
pnpm --filter @/db db:generate  # regenerate Prisma client
pnpm --filter @/db db:studio    # open Prisma Studio
```

### Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string |
| `REDIS_URL` | Redis connection string |
| `EVAL_SERVICE_URL` | URL of the eval service |

## Key Design Decisions

**No `settled_count` column.** Every worker settle issues a `SELECT ... FOR UPDATE` on the run row and recounts via `COUNT`. This avoids a race condition where two concurrent updates could both read a stale counter and both believe they are not the last job.

**Snapshotted run data.** `EvalTestCase` copies `user_input` and `reference` at run creation. `pass_threshold` is also snapshotted. Changes to the dataset or configuration after a run starts have no effect on that run.

**Detached webhooks.** Webhook POSTs are fire-and-forget (`void fetch(...).catch(() => {})`). A dead webhook URL never fails a job or causes a BullMQ retry.

**Stateless eval service.** `@/eval` has no DB access. All persistence lives in `@/core`. This keeps the eval service horizontally scalable and replaceable.

## Monorepo Commands

```bash
pnpm build          # build all packages
pnpm dev            # dev mode (persistent watchers)
pnpm typecheck      # type-check all packages
pnpm lint           # lint all packages
pnpm test           # run all tests
```

Tasks run in dependency order via Turborepo: `@/config` → `@/contracts` + `@/db` → `@/core` → `@/dashboard`.
