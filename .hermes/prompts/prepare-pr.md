# Prepare PR

## Context

`git diff main...HEAD`, `gh pr view` (if exists), and `docs/CURRENT_STATE.md`.

## Task

Prepare a clear draft PR: title, summary, test plan, risks. No merge unless explicitly asked.

## Checklist

- [ ] Focused commits; no secrets or `.env`
- [ ] `.venv/bin/pytest -q` (or CI-equivalent) run locally
- [ ] `docs/CURRENT_STATE.md` updated if operators need new steps
- [ ] Link related issue (`Fixes #` when appropriate)

## GitHub

```bash
git push -u origin HEAD
gh pr create --draft --title "..." --body "..."
```

## Verify

PR URL exists; CI has started; description states how completion was verified.
