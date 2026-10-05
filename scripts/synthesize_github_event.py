#!/usr/bin/env python3
"""Build a webhook-shaped event JSON from an issue/PR number (Actions workflow_dispatch)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _gh_json(path: str) -> dict:
    raw = subprocess.check_output(["gh", "api", path], text=True)
    return json.loads(raw)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--number", type=int, required=True)
    p.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not args.repo:
        print("Set GITHUB_REPOSITORY or pass --repo", file=sys.stderr)
        return 1
    issue = _gh_json(f"repos/{args.repo}/issues/{args.number}")
    if issue.get("pull_request"):
        pr = _gh_json(f"repos/{args.repo}/pulls/{args.number}")
        event = {
            "action": "opened",
            "pull_request": pr,
            "repository": {"full_name": args.repo},
        }
    else:
        event = {
            "action": "opened",
            "issue": issue,
            "repository": {"full_name": args.repo},
        }
    args.output.write_text(json.dumps(event), encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
