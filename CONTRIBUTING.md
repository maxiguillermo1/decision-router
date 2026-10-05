# Contributing

## Setup

```bash
git clone git@github.com:maxiguillermo1/decision-router.git
cd decision-router
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
```

## Pull requests

- Keep changes focused; add tests for new routing rules.
- CI runs `pytest` on every push/PR (see `.github/workflows/ci.yml`).
- Routing workflows only add labels — never auto-merge or auto-close.

## Optional Jev backend

```bash
export TYPESAFE_API_KEY=...
pip install -e ".[jev]"
python github_route.py --backend jev --event tests/fixtures/issue_opened.json --no-queue
```
