"""Map router destinations to GitHub label names (safe for gh label create)."""

from __future__ import annotations

ISSUE_LABELS: dict[str, str] = {
    "triage": "router-triage",
    "human": "router-human",
    "security": "router-security",
    "ignore": "router-noise",
    "review": "router-triage",
}

PR_LABELS: dict[str, str] = {
    "wait_ci": "router-wip",
    "request_review": "router-needs-review",
    "human": "router-human-review",
    "skip_noise": "router-low-touch",
    "review": "router-triage",
}


def label_for_destination(kind: str, destination: str) -> str | None:
    if kind == "pull_request":
        return PR_LABELS.get(destination)
    if kind == "issue":
        return ISSUE_LABELS.get(destination)
    return None
