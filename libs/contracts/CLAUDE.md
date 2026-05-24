# libs/contracts

Single source of truth for the `/evaluate` contract between the TypeScript core service and the Python eval service.

## Files

- `src/evaluate.ts` — Zod schemas (TypeScript). This is the canonical definition.
- `evaluate_contract.py` — Pydantic mirror (Python). Must be kept in sync with the Zod schemas manually.

## Rules

- No drift enforcement tooling — sync is manual and deliberate.
- When you change `EvaluateRequest` or `EvaluateResponse`, update both files in the same commit.
- Do not add fields to one side without adding them to the other.
- The Python file is used directly by `apps/service/eval`. Do not move it.
- No other contracts live here. One route, one file.
