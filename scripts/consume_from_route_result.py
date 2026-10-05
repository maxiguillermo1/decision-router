#!/usr/bin/env python3
"""Mark the queue job referenced by route-result.json (CI demo worker)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("route_result", type=Path, help="route-result.json from Actions")
    p.add_argument("--mark", choices=("processing", "done"), default="done")
    args = p.parse_args()
    route = json.loads(args.route_result.read_text(encoding="utf-8"))
    job_path = route.get("queue_job")
    if not job_path:
        dest = route.get("destination", "triage")
        folder = Path("queue") / "github" / dest
        jobs = sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime)
        if not jobs:
            print(json.dumps({"error": "no queue job", "destination": dest}))
            return 1
        job = jobs[-1]
    else:
        job = Path(job_path)
    if not job.is_file():
        print(json.dumps({"error": "missing job file", "path": str(job)}))
        return 1
    data = json.loads(job.read_text(encoding="utf-8"))
    data["status"] = args.mark
    job.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        "consumed": str(job),
        "status": args.mark,
        "destination": route.get("destination"),
        "repo": route.get("repo"),
        "number": route.get("number"),
        "kind": route.get("kind"),
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
