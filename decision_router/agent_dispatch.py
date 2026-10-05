"""Spawn policy and prompts for post-route workers (Cursor cloud or template fallback)."""

from __future__ import annotations

import json
from typing import Any, Mapping

# Destinations that get a worker; cheap router already filtered noise.
AGENT_DESTINATIONS: frozenset[str] = frozenset(
    {
        "triage",
        "human",
        "security",
        "request_review",
    }
)

_SKIP_DESTINATIONS: frozenset[str] = frozenset(
    {
        "ignore",
        "skip_noise",
        "wait_ci",
    }
)


def should_spawn_agent(route: Mapping[str, Any]) -> bool:
    dest = str(route.get("destination") or "")
    if dest in _SKIP_DESTINATIONS:
        return False
    return dest in AGENT_DESTINATIONS


def issue_url(route: Mapping[str, Any]) -> str | None:
    repo = route.get("repo")
    num = route.get("number")
    if not repo or not num:
        return None
    kind = route.get("kind")
    if kind == "pull_request":
        return f"https://github.com/{repo}/pull/{num}"
    return f"https://github.com/{repo}/issues/{num}"


def build_cursor_prompt(route: Mapping[str, Any]) -> str:
    state = route.get("state") or {}
    url = issue_url(route) or "(unknown)"
    dest = route.get("destination")
    kind = route.get("kind", "issue")
    return (
        "You are the automated triage agent for the decision-router lab repo.\n\n"
        f"Target ({kind}): {url}\n"
        f"Router destination bucket: {dest}\n"
        f"Router choice: {route.get('choice')} (confidence {route.get('confidence')})\n\n"
        "Do this in order:\n"
        "1. Inspect the linked GitHub issue or PR in the repository (read title, body, labels).\n"
        "2. Produce a single markdown comment for maintainers: summary, recommended next steps, "
        "whether a human must act today.\n"
        "3. Do NOT merge, close, approve, or post to external networks. Do not open PRs.\n"
        "4. If destination is security, keep the comment minimal; do not paste exploit payloads.\n\n"
        "End your reply with only the markdown body to post on GitHub (no preamble).\n\n"
        "Router state JSON:\n"
        f"{json.dumps(state, indent=2, ensure_ascii=False)[:3500]}\n"
    )


def build_template_comment(route: Mapping[str, Any], issue: Mapping[str, Any] | None) -> str:
    """Deterministic worker when CURSOR_API_KEY is absent (CI still fully automatic)."""
    dest = route.get("destination")
    url = issue_url(route) or "n/a"
    title = (issue or {}).get("title") or route.get("state", {}).get("title") or "(no title)"
    labels = (issue or {}).get("labels") or route.get("state", {}).get("labels") or []
    label_names = ", ".join(f"`{x}`" for x in labels) if labels else "_none_"

    actions: list[str]
    if dest == "security":
        actions = [
            "Treat as security-sensitive; restrict discussion on the public thread.",
            "Open a private channel for details if needed.",
            "Do not merge until a human signs off.",
        ]
    elif dest == "request_review":
        actions = [
            "Confirm CI is green before merge.",
            "Request review from a code owner if diff is non-trivial.",
            "Resolve router label after human review.",
        ]
    elif dest == "triage":
        actions = [
            "Classify: bug / docs / question / duplicate.",
            "Add project labels beyond `router-*` if missing.",
            "Assign an owner or close if duplicate/noise.",
        ]
    else:
        actions = [
            "Acknowledge the report and set expectations for follow-up.",
            "Link related issues or docs if obvious.",
            "Escalate only if urgency score was high in the route artifact.",
        ]

    action_lines = "\n".join(f"- {a}" for a in actions)
    return (
        "## Decision router (automated agent)\n\n"
        "_Template worker — add repo secret `CURSOR_API_KEY` for Cursor cloud triage._\n\n"
        f"| Field | Value |\n| --- | --- |\n"
        f"| link | {url} |\n"
        f"| title | {title} |\n"
        f"| destination | `{dest}` |\n"
        f"| labels | {label_names} |\n\n"
        "### Suggested next steps\n"
        f"{action_lines}\n\n"
        "Queue job marked `done` by Actions. No manual artifact download required.\n"
    )
