#!/usr/bin/env python3
"""Pick the oldest queued job in a folder (idempotent demo worker)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("folder", type=Path, help="e.g. queue/research")
    p.add_argument("--mark", choices=("processing", "done"), default="processing")
    args = p.parse_args()
    jobs = sorted(args.folder.glob("*.json"), key=lambda p: p.stat().st_mtime)
    if not jobs:
        print("No jobs.")
        return 0
    job = jobs[0]
    data = json.loads(job.read_text(encoding="utf-8"))
    data["status"] = args.mark
    job.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({"consumed": str(job), "status": args.mark, "goal": data.get("goal")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
