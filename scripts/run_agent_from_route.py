#!/usr/bin/env python3
"""Consume route-result.json: run triage agent, post comment, mark queue done."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from decision_router.agent_dispatch import (  # noqa: E402
    build_cursor_prompt,
    build_template_comment,
    should_spawn_agent,
)
from decision_router.github_comment import post_route_comment  # noqa: E402


def _load_route(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _mark_queue(route: dict[str, Any], mark: str) -> dict[str, Any]:
    job_path = route.get("queue_job")
    if not job_path:
        dest = route.get("destination", "triage")
        folder = Path("queue") / "github" / dest
        jobs = sorted(folder.glob("*.json"), key=lambda x: x.stat().st_mtime)
        if not jobs:
            return {"error": "no queue job", "destination": dest}
        job = jobs[-1]
    else:
        job = Path(job_path)
    if not job.is_file():
        return {"error": "missing job file", "path": str(job)}
    data = json.loads(job.read_text(encoding="utf-8"))
    data["status"] = mark
    job.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "consumed": str(job),
        "status": mark,
        "destination": route.get("destination"),
        "repo": route.get("repo"),
        "number": route.get("number"),
        "kind": route.get("kind"),
    }


def _fetch_issue(repo: str, number: int, kind: str) -> dict[str, Any] | None:
    entity = "pr" if kind == "pull_request" else "issue"
    proc = subprocess.run(
        [
            "gh",
            entity,
            "view",
            str(number),
            "--repo",
            repo,
            "--json",
            "title,body,labels",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    return json.loads(proc.stdout)


def _run_cursor(prompt: str, repo: str) -> dict[str, Any]:
    from cursor_sdk import Agent, AgentOptions, CloudAgentOptions, CursorAgentError

    api_key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not api_key:
        return {"backend": "cursor", "error": "CURSOR_API_KEY not set"}

    repo_url = f"https://github.com/{repo}"
    try:
        result = Agent.prompt(
            prompt,
            AgentOptions(
                api_key=api_key,
                model="composer-2.5",
                cloud=CloudAgentOptions(
                    repos=[{"url": repo_url, "starting_ref": "main"}],
                    skip_reviewer_request=True,
                    auto_create_pr=False,
                ),
            ),
        )
    except CursorAgentError as err:
        return {
            "backend": "cursor",
            "error": err.message,
            "retryable": err.is_retryable,
        }

    text = str(result.result or "").strip()
    return {
        "backend": "cursor",
        "status": str(result.status),
        "run_id": result.id,
        "agent_id": result.agent_id,
        "comment_body": text,
    }


def _skip_comment(route: dict[str, Any]) -> str:
    dest = route.get("destination")
    return (
        "## Decision router (automated)\n\n"
        f"No agent spawned for destination `{dest}` (noise / wait-for-CI path).\n"
        "Router triage comment above is sufficient.\n"
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("route_result", type=Path)
    p.add_argument("--mark", default="done")
    p.add_argument(
        "--backend",
        choices=("auto", "cursor", "template"),
        default="auto",
        help="auto: cursor if CURSOR_API_KEY else template",
    )
    p.add_argument("--dry-run", action="store_true", help="Do not post GitHub comment")
    args = p.parse_args()

    route = _load_route(args.route_result)
    repo = route.get("repo")
    number = route.get("number")
    kind = route.get("kind") or "issue"

    summary: dict[str, Any] = {"spawned": False}

    if not should_spawn_agent(route):
        body = _skip_comment(route)
        summary.update({"spawned": False, "reason": "destination_skip", "backend": "none"})
    else:
        backend = args.backend
        if backend == "auto":
            backend = "cursor" if os.environ.get("CURSOR_API_KEY", "").strip() else "template"

        if backend == "cursor":
            prompt = build_cursor_prompt(route)
            agent_out = _run_cursor(prompt, str(repo))
            if agent_out.get("error") and args.backend == "auto":
                issue = _fetch_issue(str(repo), int(number), kind) if repo and number else None
                body = build_template_comment(route, issue)
                summary.update({"backend": "template", "cursor_fallback": agent_out.get("error")})
            else:
                body = agent_out.get("comment_body") or build_template_comment(route, None)
                if not body.startswith("##"):
                    body = "## Decision router (Cursor agent)\n\n" + body
                summary.update(agent_out)
                summary["spawned"] = True
        else:
            issue = _fetch_issue(str(repo), int(number), kind) if repo and number else None
            body = build_template_comment(route, issue)
            summary.update({"backend": "template", "spawned": True})

    queue_info = _mark_queue(route, args.mark)
    summary.update(queue_info)

    if not args.dry_run and repo and number and body:
        post_route_comment(str(repo), int(number), body)
        summary["comment_posted"] = True

    print(json.dumps(summary, indent=2))
    if summary.get("error") and not summary.get("consumed"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
