# Fix CI

## Context

Read the failing GitHub Actions log (`gh run view --log-failed` or the PR checks tab). Note job name, step, and first error — not the whole log.

## Task

Fix the root cause in this repository. Prefer fixing the product/test over weakening CI unless the check is wrong.

## Workflow

1. Reproduce locally when possible (same command as the workflow).
2. Patch, commit on the PR branch.
3. Push and wait for checks (or `act` if you use it locally).

## Decision layer

If failure type is ambiguous (flake vs real regression), use `rules` backend on a compact state dict:

`goal`, `last_error`, `changed_files`, `test_summary`, `available_actions`: inspect | fix_test | fix_product | retry_ci | blocked

Low confidence → you reason; do not auto-merge.

## Done when

Required workflows are green on the PR branch.
