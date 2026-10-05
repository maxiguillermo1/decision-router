# Continue from checkpoint

You are Hermes resuming work on **decision-router** (or a repo that uses the same checkpoint schema).

## Before coding

1. Run: `python scripts/task_checkpoint.py resume <task_id>` (from repo root). If `stale_repo` is true, re-read the diff and CI since the recorded commit.
2. Read `docs/CURRENT_STATE.md` and `AGENTS.md`.
3. `git status` and `git log -3 --oneline` — reconcile with checkpoint `repo_identity`.

## Outcome

Complete the checkpoint `goal` without repeating completed steps listed in the checkpoint file. Use `scripts/task_checkpoint.py step` after each durable milestone.

## Verify done

- Requested artifact exists (file, PR, or green check).
- `outcome_verified` style checks pass (tests you ran, PR URL, issue comment).
- Record final decision JSON via `task_checkpoint.py decide`.

## Limits

Respect checkpoint `budget`; escalate to human if `BudgetExhausted`. Jev/routing only — never bypass failing tests or branch protection.
