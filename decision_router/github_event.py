"""Build decision state from a GitHub webhook / Actions event payload."""

from __future__ import annotations

from typing import Any, Mapping

_SECURITY = (
    "cve",
    "vulnerability",
    "exploit",
    "secret",
    "credential",
    "auth bypass",
    "rce",
    "xss",
    "sql injection",
)
_SPAM = (
    "crypto giveaway",
    "claim your",
    "whatsapp me",
    "seo services",
    "buy followers",
)
_WIP = ("wip", "draft", "do not merge", "[skip ci]")


def state_from_event(event: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return (kind, state) where kind is 'issue' | 'pull_request' | 'unknown'."""
    if "pull_request" in event:
        pr = event["pull_request"]
        title = str(pr.get("title") or "")
        body = str(pr.get("body") or "")[:4000]
        labels = [lb.get("name", "") for lb in pr.get("labels") or []]
        return "pull_request", {
            "event": event.get("action", "unknown"),
            "title": title,
            "body_excerpt": body[:2000],
            "labels": labels,
            "draft": bool(pr.get("draft")),
            "additions": int(pr.get("additions") or 0),
            "deletions": int(pr.get("deletions") or 0),
            "changed_files": int(pr.get("changed_files") or 0),
            "author_association": str(pr.get("author_association") or ""),
            "repo": _repo_slug(event),
            "number": int(pr.get("number") or 0),
        }
    if "issue" in event:
        issue = event["issue"]
        if issue.get("pull_request"):
            return "unknown", {"event": event.get("action", "unknown")}
        title = str(issue.get("title") or "")
        body = str(issue.get("body") or "")[:4000]
        labels = [lb.get("name", "") for lb in issue.get("labels") or []]
        return "issue", {
            "event": event.get("action", "unknown"),
            "title": title,
            "body_excerpt": body[:2000],
            "labels": labels,
            "author_association": str(issue.get("author_association") or ""),
            "repo": _repo_slug(event),
            "number": int(issue.get("number") or 0),
        }
    return "unknown", {"event": event.get("action", "unknown")}


def _repo_slug(event: Mapping[str, Any]) -> str:
    repo = event.get("repository") or {}
    return str(repo.get("full_name") or "")


def text_blob(state: Mapping[str, Any]) -> str:
    return f"{state.get('title', '')}\n{state.get('body_excerpt', '')}".lower()


def looks_security(state: Mapping[str, Any]) -> bool:
    t = text_blob(state)
    return any(s in t for s in _SECURITY)


def looks_spam(state: Mapping[str, Any]) -> bool:
    t = text_blob(state)
    return any(s in t for s in _SPAM)


def looks_wip(state: Mapping[str, Any]) -> bool:
    title = str(state.get("title") or "").lower()
    return bool(state.get("draft")) or any(w in title for w in _WIP)
