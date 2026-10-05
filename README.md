# decision-router

[![ci](https://github.com/maxiguillermo1/decision-router/actions/workflows/ci.yml/badge.svg)](https://github.com/maxiguillermo1/decision-router/actions/workflows/ci.yml)

Cheap **pick / score / gate** layer for agent loops — Jev-shaped API without requiring TypeSafe on day one.

**If it creates → frontier LLM. If it picks → here. If it executes → code** (limits, persistence, human gates on irreversible actions).

Repository: https://github.com/maxiguillermo1/decision-router

## Quick start

```bash
git clone git@github.com:maxiguillermo1/decision-router.git
cd decision-router
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python chief.py --goal "Research Jev gateways" --completed-work "Nothing yet."
.venv/bin/pytest -q
```

With a TypeSafe key:

```bash
export TYPESAFE_API_KEY=...
.venv/bin/pip install "typesafe-sdk"
.venv/bin/python chief.py --backend jev --goal "..." --completed-work "..."
```

## Layout

| Piece | Role |
| ----- | ---- |
| `decision_router/backends/rules.py` | Zero-cost heuristics (briefing router + X engage gate) |
| `decision_router/backends/jev.py` | Optional `typesafe-sdk` `system_one` |
| `chief.py` | Morning-briefing handoff → `queue/research|write|review/*.json` |
| `engage_gate.py` | Playbook pattern F — skip / draft_* / escalate (never auto-post) |
| `github_route.py` | Issues/PRs → `router-*` labels + optional `queue/github/` JSON |
| `scripts/consume_one.py` | Demo worker: oldest job → status bump |
| `.github/workflows/route-github-event.yml` | On issue/PR open: route → artifact + label + triage comment |
| `.github/workflows/consume-github-queue.yml` | After route succeeds: demo worker marks queue job `done` + comment |

## Confidence floor

Default `0.85` is a **policy gate**, not accuracy. Low confidence routes to `review` (or skip for engage). Calibrate on your own labeled examples.

## GitHub

Local replay of an event fixture:

```bash
.venv/bin/python github_route.py --event tests/fixtures/issue_opened.json --no-queue
```

On **this repo**, the loop is fully automatic:

1. Open or reopen an issue/PR → **route-github-event** runs (rules, or Jev if `TYPESAFE_API_KEY` secret is set).
2. You get a **triage comment**, optional `router-*` label (confidence ≥ 0.85 + safe_auto), and artifact `github-route-<run_id>` (`route-result.json` + `queue/github/...`).
3. **consume-github-queue** runs on success → demo worker sets queue job `done` and posts a second comment.

Re-run without a new issue: Actions → **route-github-event** → Run workflow → enter issue/PR number.

Optional repo secret: `TYPESAFE_API_KEY` for `--backend auto` on ambiguous traffic only (add later); rules-only works with no secrets.

Wire to your org: fork, tune heuristics in `decision_router/backends/rules.py`, or swap `--backend jev` when you have TypeSafe credentials.

## Wire to Hermes / Maxi

1. Hermes cron or hook: build `state` from session metadata → run `chief.py --json` → spawn worker only for matching queue folder.
2. GitHub Actions → download route artifact → Hermes worker consumes `queue/github/<destination>/*.json`.
3. Maxi: same JSON schema as inbox handoff; rules backend mirrors classify-first / SAFE_AUTO before LLM.
4. Replace rules with `--backend jev` when signups/keys are available (Vercel AI Gateway `typesafe-ai/jev`, Cloudflare `typesafe/jev`).

## Guardrails (from playbook)

- Action and spend limits in workers, not in the decider.
- Save progress after each tool call.
- Publishing / X: drafts to review folder only.
- Outcome check after DONE (did the file actually land?).
