# decision-router — agent entry

Canonical repo for **cheap routing** (Choice / Score / Noul) between Hermes (reasoning) and code (execution). GitHub: https://github.com/maxiguillermo1/decision-router

## Startup

1. `git status` — work on a branch; do not commit secrets.
2. Read `docs/CURRENT_STATE.md` for goal, wiring, and blockers.
3. `python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"` then `.venv/bin/pytest -q`.

## Division of labor

| Layer | Role |
| ----- | ---- |
| Hermes / frontier LLM | Goals, ambiguous fixes, PR prose |
| Jev (`TYPESAFE_API_KEY`) | Gray-zone routing only when rules confidence &lt; floor |
| This repo (rules + scripts) | Heuristics, queues, GitHub Actions, budgets, checkpoints |

Jev never overrides branch protection, tests, or spend limits — workers enforce those.

## Key commands

```bash
.venv/bin/python github_route.py --event tests/fixtures/issue_opened.json --no-queue
.venv/bin/python chief.py --goal "..." --completed-work "..."
.venv/bin/python scripts/task_checkpoint.py create --goal "..." --repo .
```

Hermes continuation prompts: `.hermes/prompts/`.

## Optional backends

- **Rules** (default): zero cost.
- **Jev**: `pip install -e ".[jev]"`, `export TYPESAFE_API_KEY=...` (see https://jevwiki.ai/wiki/guides/quickstart.md). Gateway: set `TYPESAFE_BASE_URL` per TypeSafe docs.
- **Cursor triage**: repo secret `CURSOR_API_KEY` on GitHub only.

## Do not

- Auto-merge, auto-close production issues, or post to social without human review.
- Store API keys in git; use env / GitHub secrets.
