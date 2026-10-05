#!/usr/bin/env python3
"""Create, update, and resume task checkpoints for Hermes ↔ GitHub loops."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decision_router.checkpoint import (  # noqa: E402
    DEFAULT_CHECKPOINT_ROOT,
    append_step,
    enforce_budget,
    load_checkpoint,
    new_checkpoint,
    record_decision,
    record_error,
    refresh_repo_identity,
    repo_stale,
    save_checkpoint,
)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Task checkpoint store")
    p.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_CHECKPOINT_ROOT,
        help="Checkpoint directory (default: .decision-router/checkpoints)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    create = sub.add_parser("create", help="Start a new checkpoint")
    create.add_argument("--goal", required=True)
    create.add_argument("--repo", type=Path, default=None)
    create.add_argument("--task-id", default=None)

    show = sub.add_parser("show", help="Print checkpoint JSON")
    show.add_argument("task_id")

    refresh = sub.add_parser("refresh", help="Refresh git evidence on disk")
    refresh.add_argument("task_id")

    step = sub.add_parser("step", help="Append a completed step")
    step.add_argument("task_id")
    step.add_argument("text")

    decide = sub.add_parser("decide", help="Append a decision record (JSON object)")
    decide.add_argument("task_id")
    decide.add_argument("payload", help="JSON object")

    resume = sub.add_parser("resume", help="Stale check + budget gate; print summary")
    resume.add_argument("task_id")

    return p.parse_args()


def main() -> int:
    args = _parse_args()
    root = args.root

    if args.cmd == "create":
        cp = new_checkpoint(goal=args.goal, repo_path=args.repo, task_id=args.task_id)
        path = save_checkpoint(root, cp)
        print(json.dumps({"task_id": cp["task_id"], "path": str(path)}, indent=2))
        return 0

    cp = load_checkpoint(root, args.task_id)

    if args.cmd == "show":
        print(json.dumps(cp, indent=2))
        return 0

    if args.cmd == "refresh":
        refresh_repo_identity(cp)
        save_checkpoint(root, cp)
        print(json.dumps({"task_id": cp["task_id"], "repo_identity": cp["repo_identity"]}, indent=2))
        return 0

    if args.cmd == "step":
        append_step(cp, args.text)
        save_checkpoint(root, cp)
        print(json.dumps({"task_id": cp["task_id"], "step": args.text}, indent=2))
        return 0

    if args.cmd == "decide":
        payload = json.loads(args.payload)
        record_decision(cp, payload)
        save_checkpoint(root, cp)
        print(json.dumps({"task_id": cp["task_id"], "decision": payload}, indent=2))
        return 0

    if args.cmd == "resume":
        stale = repo_stale(cp)
        try:
            enforce_budget(cp)
            budget_ok = True
            budget_err = None
        except Exception as e:
            budget_ok = False
            budget_err = str(e)
        summary = {
            "task_id": cp["task_id"],
            "goal": cp.get("goal"),
            "stale_repo": stale,
            "budget_ok": budget_ok,
            "budget_error": budget_err,
            "pending": cp.get("pending"),
            "last_error": (cp.get("errors") or [None])[-1],
            "completed_steps": len(cp.get("completed_steps") or []),
        }
        if stale:
            refresh_repo_identity(cp)
            save_checkpoint(root, cp)
            summary["refreshed_repo_identity"] = cp.get("repo_identity")
        print(json.dumps(summary, indent=2))
        return 0 if budget_ok else 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
