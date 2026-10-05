#!/usr/bin/env python3
"""Chief of Staff handoff — rules backend by default; Jev when TYPESAFE_API_KEY is set."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from decision_router import system_one
from decision_router.handoff import enqueue_handoff
from decision_router.recipes import BRIEFING_NEXT_WORKER, BRIEFING_URGENCY, SAFE_TO_RUN
from decision_router.types import DEFAULT_CONFIDENCE_FLOOR


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Route a goal into queue/research|write|review")
    p.add_argument("--goal", help="Goal text (or prompt)")
    p.add_argument("--completed-work", default="", help="Work done so far")
    p.add_argument(
        "--backend",
        choices=("auto", "rules", "jev"),
        default="auto",
        help="Decision backend (auto: jev if TYPESAFE_API_KEY else rules)",
    )
    p.add_argument(
        "--confidence-floor",
        type=float,
        default=DEFAULT_CONFIDENCE_FLOOR,
        help="Min confidence to honor choice (not accuracy)",
    )
    p.add_argument(
        "--queue",
        type=Path,
        default=Path(__file__).resolve().parent / "queue",
        help="Queue root directory",
    )
    p.add_argument("--json", action="store_true", help="Print job path and payload summary as JSON")
    return p.parse_args()


def _pick_backend(name: str) -> str:
    if name == "jev":
        return "jev"
    if name == "rules":
        return "rules"
    if os.environ.get("TYPESAFE_API_KEY"):
        return "jev"
    return "rules"


def main() -> int:
    args = _parse_args()
    goal = (args.goal or "").strip() or input("Goal: ").strip()
    if not goal:
        print("Enter a goal.", file=sys.stderr)
        return 1
    notes = (args.completed_work or "").strip() or input("Completed work: ").strip() or "Nothing yet."

    state = {"goal": goal, "completed_work": notes}
    backend_name = _pick_backend(args.backend)

    try:
        if backend_name == "jev":
            result = system_one(
                state,
                {
                    "next_worker": BRIEFING_NEXT_WORKER,
                    "urgency": BRIEFING_URGENCY,
                    "safe_to_run": SAFE_TO_RUN,
                },
                backend="jev",
            )
        else:
            result = system_one(
                state,
                {
                    "next_worker": BRIEFING_NEXT_WORKER,
                    "urgency": BRIEFING_URGENCY,
                    "safe_to_run": SAFE_TO_RUN,
                },
                backend="rules",
            )
    except RuntimeError as e:
        print(f"Backend error: {e}", file=sys.stderr)
        return 2

    job = enqueue_handoff(
        args.queue,
        state,
        result,
        confidence_floor=args.confidence_floor,
        allowed_destinations={"research", "write", "review"},
    )

    if args.json:
        payload = json.loads(job.read_text(encoding="utf-8"))
        print(json.dumps({"job": str(job), "payload": payload}, indent=2))
    else:
        print(f"backend={result.backend}")
        print(f"choice={result.choices['next_worker'].choice}")
        print(f"confidence={result.choices['next_worker'].confidence}")
        print(f"destination={payload_destination(job)}")
        print(f"Saved handoff: {job}")
    return 0


def payload_destination(job: Path) -> str:
    data = json.loads(job.read_text(encoding="utf-8"))
    return str(data.get("destination", "?"))


if __name__ == "__main__":
    raise SystemExit(main())
