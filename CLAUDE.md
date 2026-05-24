# rag-evaluation-platform

## Architecture

Monorepo: pnpm workspaces + Turborepo. Scoped packages: `@/*`.

### Services

- `apps/web/dashboard` — React SPA (Vite). Hono RPC `hc` typed client.
- `apps/service/core` — Hono API + BullMQ worker (two entrypoints, one package).
- `apps/service/eval` — Python FastAPI + RAGAS (uv). Stateless. One job per test case. Entry point: `main.py`. Receives jobs via HTTP POST to `/evaluate`. Errors are returned as HTTP error responses; `@/core` maps them to the `error` outcome. No direct DB access — results returned to `@/core` via the `/evaluate` response contract.

### Libs

- `libs/config` — shared tsconfig + eslint. Everything imports this first.
- `libs/contracts` — `/evaluate` request/response shape. Zod (TS) + Pydantic (Python) mirrors, hand-written, kept in sync manually. **When modifying any type here, always update both the Zod schema and the Pydantic model in the same change. Never modify one without the other.**
- `libs/db` — Prisma schema + generated client. **Sole owner of the schema.** No other package touches the Prisma schema file.

### Allowed seams (only these three)

1. Dashboard imports `@/core/app-type` (type-only) for the `hc` typed client.
2. TS ↔ Python boundary via `libs/contracts` only.
3. Apps consume libs; libs never depend on apps.

## Critical invariants

### `apps/service/core` — import direction

`src/shared/` contains the Prisma client singleton, BullMQ queue definitions, and run-completion logic. Both entrypoints (`app.ts` for the Hono API, `worker.ts` for BullMQ) import **down** into `src/shared/`. Neither entrypoint imports the other. Violating this creates circular dependency risk and makes the split between API and worker processes unclear.

### `apps/service/core` — detached webhook invariant

Webhook `fetch` calls are always fire-and-forget: `void fetch(...).catch(() => {})`. They must never be awaited, never throw into the job handler, and never cause a BullMQ retry. A dead webhook URL must not fail a job or cause the run-completion transaction to re-run.

### `apps/service/core` — run completion

No `settled_count` column. Each job settle runs one transaction:

1. Update the test-case row.
2. `SELECT ... FOR UPDATE` on the `EvalRun` row.
3. Recount settled test cases.
4. Complete the run only if `settled == total_count`.

`success`/`failed` = model quality outcome. `error` = infrastructure failure. An `error` outcome still settles the test-case row (step 1) and participates in the recount (steps 2–4). A run can complete with a mix of `success`, `failed`, and `error` outcomes.

### `libs/db` — sole owner boundary

Only `libs/db` writes Prisma schema. Only `libs/db` runs `prisma migrate` and `prisma generate`. Other packages import the generated client from `@/db`, never from a local path.

## Never do these

- Add Prisma imports outside `@/db`
- Add direct DB access in `@/eval`
- Await webhook fetches in `@/core`
- Add a `settled_count` column — it does not exist by design; the worker recounts on every settle
- Modify only one side of a `libs/contracts` type — both Zod and Pydantic must change together

## Local dev

```bash
cp .env.example .env
docker compose up -d        # Postgres + Redis
pnpm install
pnpm turbo run build        # should no-op cleanly on empty stubs
```

Start the Python eval service separately (not driven by Turborepo):

```bash
cd apps/service/eval && uv run fastapi dev
```

`@/eval` has a stub `package.json` (uv shim) so Turborepo can reference it in the workspace graph, but `turbo run build` does not execute Python tasks. Python dev/test is managed via `uv` directly.

## Package names

| Path                 | Package name       |
| -------------------- | ------------------ |
| `apps/web/dashboard` | `@/dashboard`      |
| `apps/service/core`  | `@/core`           |
| `apps/service/eval`  | `@/eval` (uv shim) |
| `libs/config`        | `@/config`         |
| `libs/contracts`     | `@/contracts`      |
| `libs/db`            | `@/db`             |
