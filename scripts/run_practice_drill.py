#!/usr/bin/env python3
"""Open a practice issue; route-github-event + consume-github-queue run automatically."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decision_router.practice_drill import drill_title, pick_scenario  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--scenario",
        default="random",
        choices=["random", "security", "bug", "spam", "triage"],
    )
    p.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
        help="owner/name (default: GITHUB_REPOSITORY)",
    )
    args = p.parse_args()
    repo = args.repo.strip()
    if not repo:
        print("Set GITHUB_REPOSITORY or pass --repo", file=sys.stderr)
        return 1

    scenario = pick_scenario(args.scenario)
    title = drill_title(scenario)
    body = (
        f"{scenario.body}\n\n"
        f"---\n"
        f"_Scenario `{scenario.key}` · expected destination `{scenario.expected_destination}` · "
        f"closes automatically after the triage agent runs._\n"
    )

    subprocess.run(
        ["gh", "label", "create", "lab-drill", "--repo", repo, "--force", "--color", "1d76db"],
        check=True,
        capture_output=True,
    )

    proc = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
            "--label",
            "lab-drill",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    url = proc.stdout.strip()
    number = url.rstrip("/").split("/")[-1]

    out = {
        "scenario": scenario.key,
        "expected_destination": scenario.expected_destination,
        "issue_url": url,
        "number": int(number) if number.isdigit() else number,
        "repo": repo,
        "note": "route-github-event and consume-github-queue will run without manual steps",
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
