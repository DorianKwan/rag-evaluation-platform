# libs/db

Sole owner of the Prisma schema and generated client for the entire monorepo.

## Boundary rules

- Only this package runs `prisma migrate` or `prisma generate`.
- Other packages import types and the client from `@/db` — never from a local path.
- Do not add application logic here. This package exposes the Prisma client and generated types only.

## Models and table names (all singular)

| Model             | Table               |
| ----------------- | ------------------- |
| `Dataset`         | `dataset`           |
| `DatasetTestCase` | `dataset_test_case` |
| `EvalRun`         | `eval_run`          |
| `EvalTestCase`    | `eval_test_case`    |

## Enums

Two separate enums — kept distinct so either can diverge without affecting the other:

- `RunStatus` — used by `EvalRun.status`
- `TestCaseStatus` — used by `EvalTestCase.status`

Both share the same values for now: `pending`, `running`, `success`, `failed`, `error` (lowercase).

## Column names (important for core's completion transaction)

The raw `FOR UPDATE` completion query in `apps/service/core` targets these exact snake_case column names:

- `eval_test_case.eval_run_id`
- `eval_test_case.status`
- `eval_run.total_count`
- `eval_run.pass_threshold`
- `eval_run.status`
- `eval_run.completed_at`

Status values are **lowercase** strings: `pending`, `running`, `success`, `failed`, `error`.
A test case is "settled" when its status is one of: `success`, `failed`, `error`.

## Key field notes

- `eval_run.pass_threshold` — snapshotted at run creation (`default 0.7`). Never updated after creation so env changes don't affect in-flight runs.
- `eval_run.total_count` — set once at creation from `DatasetTestCase` count. Workers use it for last-job detection without issuing a second `COUNT`.
- `eval_run.webhook_url` / `eval_test_case.webhook_url` — optional. Core fires the run webhook on run completion and the test-case webhook on each job settlement.
- `eval_test_case.user_input` / `eval_test_case.reference` — snapshot of `DatasetTestCase` fields at run creation time. Preserved so dataset edits don't affect historical runs.
- `eval_test_case.attempt_count` / `eval_test_case.last_error` — BullMQ retry state mirrored for observability without querying Redis.

## Schema changes

- Always run `pnpm --filter @/db db:migrate` after changing the schema.
- Always run `pnpm --filter @/db db:generate` to regenerate the client.
- Commit the migration SQL files.
