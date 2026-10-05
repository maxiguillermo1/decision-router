"""Post human-visible triage comments on issues/PRs (no auto-merge)."""

from __future__ import annotations

import json
import subprocess
from typing import Any, Mapping

from decision_router.label_policy import label_applied_note
from decision_router.types import DEFAULT_CONFIDENCE_FLOOR


def format_route_comment(
    payload: Mapping[str, Any],
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
) -> str:
    urgency = payload.get("urgency") or {}
    label = payload.get("label")
    label_line = f"`{label}`" if label else "_skipped (confidence gate)_"
    label_applied = label_applied_note(payload, confidence_floor)

    return (
        "## Decision router (automated triage)\n\n"
        "Cheap first pass only — **labels/comments, never auto-merge or auto-close.**\n\n"
        f"| Field | Value |\n| --- | --- |\n"
        f"| destination | `{payload.get('destination')}` |\n"
        f"| choice | `{payload.get('choice')}` ({payload.get('confidence'):.2f}) |\n"
        f"| backend | `{payload.get('backend')}` |\n"
        f"| urgency | `{urgency.get('label', 'n/a')}` ({urgency.get('confidence', 0):.2f}) |\n"
        f"| suggested label | {label_line} |\n"
        f"| label applied | {label_applied} |\n\n"
        "A triage agent workflow runs automatically after this job (no manual artifact download).\n"
    )


def post_route_comment(repo: str, number: int, body: str) -> None:
    subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/issues/{number}/comments",
            "--input",
            "-",
        ],
        input=json.dumps({"body": body}),
        text=True,
        check=True,
    )


def post_worker_comment(repo: str, number: int, summary: Mapping[str, Any]) -> None:
    body = (
        "## Decision router (demo worker)\n\n"
        f"Consumed oldest queue job → status `{summary.get('status')}`.\n\n"
        f"```json\n{json.dumps(summary, indent=2)}\n```\n"
    )
    post_route_comment(repo, number, body)
