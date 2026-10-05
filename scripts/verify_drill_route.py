#!/usr/bin/env python3
"""Fail CI when a practice drill did not route to the expected destination."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("drill_result", type=Path, help="Output from run_practice_drill.py")
    p.add_argument("route_result", type=Path, help="Output from github_route.py --output")
    p.add_argument("--output", type=Path, default=None, help="Write drill-report.json")
    args = p.parse_args()

    drill: dict[str, Any] = json.loads(args.drill_result.read_text(encoding="utf-8"))
    route: dict[str, Any] = json.loads(args.route_result.read_text(encoding="utf-8"))

    expected = str(drill.get("expected_destination") or "")
    actual = str(route.get("destination") or "")
    cascade = route.get("cascade") or {}

    report = {
        "scenario": drill.get("scenario"),
        "issue_url": drill.get("issue_url"),
        "expected_destination": expected,
        "actual_destination": actual,
        "choice": route.get("choice"),
        "confidence": route.get("confidence"),
        "backend": route.get("backend"),
        "cascade": cascade,
        "passed": actual == expected,
    }

    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if not report["passed"]:
        print(
            f"Drill routing mismatch: expected `{expected}`, got `{actual}`",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
