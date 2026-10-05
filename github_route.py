#!/usr/bin/env python3
"""Route GitHub issues/PRs with cheap Choice/Score/Noul — for Actions or local gh replay."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from decision_router import system_one
from decision_router.cascade import system_one_cascade
from decision_router.github_event import state_from_event
from decision_router.github_comment import format_route_comment, post_route_comment
from decision_router.github_labels import label_for_destination
from decision_router.label_policy import should_apply_routing_label
from decision_router.handoff import enqueue_handoff
from decision_router.recipes import (
    GITHUB_ISSUE_ROUTE,
    GITHUB_PR_ROUTE,
    GITHUB_SAFE_AUTO_LABEL,
    GITHUB_URGENCY,
)
from decision_router.types import DEFAULT_CONFIDENCE_FLOOR

_ISSUE_DEST = {"triage", "human", "security", "ignore"}
_PR_DEST = {"wait_ci", "request_review", "human", "skip_noise"}


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GitHub issue/PR first-pass router")
    p.add_argument(
        "--event",
        type=Path,
        default=None,
        help="Event JSON (default: GITHUB_EVENT_PATH)",
    )
    p.add_argument("--backend", default="rules", choices=("rules", "jev", "auto"))
    p.add_argument("--confidence-floor", type=float, default=DEFAULT_CONFIDENCE_FLOOR)
    p.add_argument(
        "--queue",
        type=Path,
        default=Path(__file__).resolve().parent / "queue" / "github",
        help="Enqueue under queue/github/<destination>/",
    )
    p.add_argument("--no-queue", action="store_true", help="Skip writing queue JSON")
    p.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Write full result JSON (default: stdout only)",
    )
    p.add_argument(
        "--apply-labels",
        action="store_true",
        help="Add routing label via gh (needs GITHUB_REPOSITORY + number in event)",
    )
    p.add_argument(
        "--post-comment",
        action="store_true",
        help="Post triage summary comment via gh (issues and PRs)",
    )
    return p.parse_args()


def route_event(event: dict, *, backend: str, confidence_floor: float) -> dict:
    kind, state = state_from_event(event)
    if kind == "unknown":
        return {"kind": kind, "error": "unsupported event", "state": state}

    if kind == "issue":
        questions = {
            "github_issue_route": GITHUB_ISSUE_ROUTE,
            "github_urgency": GITHUB_URGENCY,
            "github_safe_auto_label": GITHUB_SAFE_AUTO_LABEL,
        }
        choice_key = "github_issue_route"
        allowed = _ISSUE_DEST
        fallback = "triage"
    else:
        questions = {
            "github_pr_route": GITHUB_PR_ROUTE,
            "github_urgency": GITHUB_URGENCY,
            "github_safe_auto_label": GITHUB_SAFE_AUTO_LABEL,
        }
        choice_key = "github_pr_route"
        allowed = _PR_DEST
        fallback = "request_review"

    cascade_meta: dict = {"primary": backend}
    if backend == "auto":
        result, cascade_meta = system_one_cascade(
            state,
            questions,
            choice_key,
            confidence_floor=confidence_floor,
        )
    elif backend == "jev":
        result = system_one(state, questions, backend="jev")
        cascade_meta = {"primary": "jev", "escalated_to_jev": False}
    else:
        result = system_one(state, questions, backend="rules")
        cascade_meta = {"primary": "rules", "escalated_to_jev": False}

    answer = result.choices[choice_key]
    from decision_router.handoff import resolve_destination

    destination = resolve_destination(
        answer,
        allowed=allowed,
        confidence_floor=confidence_floor,
        fallback=fallback,
    )
    label = label_for_destination(kind, destination)
    safe = result.nouls.get("github_safe_auto_label")
    return {
        "kind": kind,
        "repo": state.get("repo"),
        "number": state.get("number"),
        "backend": result.backend,
        "choice": answer.choice,
        "confidence": answer.confidence,
        "destination": destination,
        "label": label,
        "urgency": (
            {"label": result.scores["github_urgency"].label, "confidence": result.scores["github_urgency"].confidence}
            if "github_urgency" in result.scores
            else None
        ),
        "safe_auto_label": (
            {"value": safe.value, "confidence": safe.confidence} if safe else None
        ),
        "state": state,
        "cascade": cascade_meta,
        "_choice_key": choice_key,
        "_result": result,
    }


def apply_label(repo: str, number: int, label: str, kind: str) -> None:
    entity = "pr" if kind == "pull_request" else "issue"
    subprocess.run(
        ["gh", "label", "create", label, "--repo", repo, "--force", "--color", "ededed"],
        check=False,
        capture_output=True,
    )
    subprocess.run(
        ["gh", entity, "edit", str(number), "--repo", repo, "--add-label", label],
        check=True,
    )


def main() -> int:
    args = _parse_args()
    event_path = args.event or os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("Pass --event or set GITHUB_EVENT_PATH", file=sys.stderr)
        return 1
    event = json.loads(Path(event_path).read_text(encoding="utf-8"))

    try:
        out = route_event(
            event, backend=args.backend, confidence_floor=args.confidence_floor
        )
    except RuntimeError as e:
        print(f"Backend error: {e}", file=sys.stderr)
        return 2

    if out.get("error"):
        print(json.dumps(out, indent=2))
        return 3

    result = out.pop("_result")
    choice_key = out.pop("_choice_key")
    job_path = None
    if not args.no_queue:
        job = enqueue_handoff(
            args.queue,
            out["state"],
            result,
            choice_key=choice_key,
            allowed_destinations=_ISSUE_DEST if out["kind"] == "issue" else _PR_DEST,
            confidence_floor=args.confidence_floor,
            fallback="triage" if out["kind"] == "issue" else "request_review",
        )
        job_path = str(job)
        out["queue_job"] = job_path

    payload = {k: v for k, v in out.items() if k != "state"}
    payload["policy"] = "Labels only — never auto-merge or auto-close."

    if args.output:
        args.output.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))

    if args.apply_labels and out.get("label") and out.get("repo") and out.get("number"):
        if should_apply_routing_label(payload, args.confidence_floor):
            apply_label(out["repo"], int(out["number"]), out["label"], out["kind"])
        else:
            print(
                "Skipped label apply: confidence/safe_auto_label gate",
                file=sys.stderr,
            )
    if args.post_comment and out.get("repo") and out.get("number"):
        post_route_comment(
            out["repo"],
            int(out["number"]),
            format_route_comment(payload),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
