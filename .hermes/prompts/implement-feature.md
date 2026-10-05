# Implement a feature

## Context

Read `docs/CURRENT_STATE.md`, relevant issue/PR on GitHub (`gh issue view` / `gh pr view`), and touched modules only.

## Task

Implement the requested feature with the smallest coherent diff. Match existing patterns in `decision_router/`.

## Workflow

1. Branch from `main` (or the issue’s linked branch).
2. Implement + unit tests in `tests/`.
3. `.venv/bin/pytest -q`
4. Update `docs/CURRENT_STATE.md` **Recent changes** if behavior changed.

## Routing (optional)

For “what next” after inspection, run rules locally:

`python github_route.py --event <fixture> --no-queue`

Use Jev only with `TYPESAFE_API_KEY` and `--backend auto` in gray-zone scenarios.

## Done when

Tests pass and behavior matches the issue acceptance criteria.
