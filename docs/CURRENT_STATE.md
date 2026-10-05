# Current state — decision-router

Updated: 2026-10-05 (post-merge)

## Goal

Connect Hermes, GitHub, and optional **Jev** so repeated routing decisions stay cheap while frontier models handle implementation. Resumable checkpoints bridge long sessions.

## Architecture

- `decision_router/backends/rules.py` — primary router (issues, PRs, morning briefing).
- `decision_router/cascade.py` — rules first; Jev only in gray-zone when `TYPESAFE_API_KEY` is set.
- `decision_router/backends/jev.py` — `typesafe-sdk` `TypeSafeClient.system_one` (live calls require key).
- `github_route.py` + `.github/workflows/route-github-event.yml` — label + queue + triage comment.
- `scripts/run_agent_from_route.py` + `consume-github-queue.yml` — post-route worker (Cursor or template).
- `decision_router/checkpoint.py` — task JSON under `.decision-router/checkpoints/` (local; not committed).

## Validation

- `pytest -q` — rules, cascade, GitHub CLI helpers, checkpoints, practice drill fixtures.
- Actions: **practice-lab-drill** (weekly + manual) exercises full GitHub loop on this repo.

## Blockers / access

| Capability | Status |
| ---------- | ------ |
| GitHub `gh` + Actions on this repo | Wired (origin `maxiguillermo1/decision-router`) |
| `TYPESAFE_API_KEY` | User-provided; direct TypeSafe signup may require gateway key (see jevwiki quickstart, 2026-09 note) |
| `CURSOR_API_KEY` | Optional secret for cloud triage agent |

## Next steps

1. Set repo secrets when you want live Jev/cascade in Actions: `gh secret set TYPESAFE_API_KEY` (and optional `CURSOR_API_KEY`).
2. Point another product repo at the same workflow pattern (fork + tune `rules.py`).
3. Calibrate `DEFAULT_CONFIDENCE_FLOOR` (0.85) on labeled examples from your org.

## Recent changes

- **Merged to `main`:** PR #6 (`aa2a3a5`) — checkpoints, Hermes prompts, `jev-latest` default.
- Checkpoints + `scripts/task_checkpoint.py` for resumable Hermes/GitHub tasks.
- `.hermes/prompts/` for standard continuation templates.
- Rules→Jev cascade in CI when `TYPESAFE_API_KEY` secret is set.
