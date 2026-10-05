"""Resumable task checkpoints — atomic JSON, duplicate side-effect guards, budget limits."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

DEFAULT_CHECKPOINT_ROOT = Path(".decision-router") / "checkpoints"


class BudgetExhausted(RuntimeError):
    """Raised when a configured limit blocks further automated actions."""


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def default_budget() -> dict[str, Any]:
    return {
        "max_actions": 50,
        "max_model_calls": 20,
        "max_retries": 5,
        "max_runtime_seconds": 3600,
    }


def new_checkpoint(
    *,
    goal: str,
    repo_path: Path | None = None,
    task_id: str | None = None,
    budget: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    tid = task_id or uuid4().hex
    repo = repo_path.resolve() if repo_path else None
    evidence = git_evidence(repo) if repo else {}
    return {
        "task_id": tid,
        "goal": goal,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "repo_path": str(repo) if repo else None,
        "repo_identity": evidence,
        "completed_steps": [],
        "decisions": [],
        "pending": [],
        "errors": [],
        "side_effect_ids": [],
        "metrics": {
            "actions": 0,
            "model_calls": 0,
            "retries": 0,
            "started_at": time.time(),
        },
        "budget": dict(budget or default_budget()),
    }


def git_evidence(repo_path: Path) -> dict[str, Any]:
    if not (repo_path / ".git").exists():
        return {"error": "not a git repository", "path": str(repo_path)}
    def _run(args: list[str]) -> str:
        proc = subprocess.run(
            args,
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            return ""
        return proc.stdout.strip()

    return {
        "commit": _run(["git", "rev-parse", "HEAD"]),
        "branch": _run(["git", "branch", "--show-current"]),
        "remote": _run(["git", "remote", "get-url", "origin"]),
        "dirty": bool(_run(["git", "status", "--porcelain"])),
        "captured_at": _now_iso(),
    }


def repo_stale(checkpoint: Mapping[str, Any], repo_path: Path | None = None) -> bool:
    """True if HEAD or dirty flag changed since checkpoint was saved."""
    identity = checkpoint.get("repo_identity") or {}
    if identity.get("error"):
        return False
    path = repo_path or (
        Path(checkpoint["repo_path"]) if checkpoint.get("repo_path") else None
    )
    if not path:
        return False
    current = git_evidence(path)
    if not current.get("commit"):
        return True
    return (
        current.get("commit") != identity.get("commit")
        or bool(current.get("dirty")) != bool(identity.get("dirty"))
    )


def refresh_repo_identity(checkpoint: dict[str, Any], repo_path: Path | None = None) -> dict[str, Any]:
    path = repo_path or (
        Path(checkpoint["repo_path"]) if checkpoint.get("repo_path") else None
    )
    if path:
        checkpoint["repo_identity"] = git_evidence(path)
    checkpoint["updated_at"] = _now_iso()
    return checkpoint


def checkpoint_path(root: Path, task_id: str) -> Path:
    return root / f"{task_id}.json"


def save_checkpoint(root: Path, checkpoint: Mapping[str, Any]) -> Path:
    tid = str(checkpoint["task_id"])
    path = checkpoint_path(root, tid)
    data = dict(checkpoint)
    data["updated_at"] = _now_iso()
    atomic_write_json(path, data)
    return path


def load_checkpoint(root: Path, task_id: str) -> dict[str, Any]:
    path = checkpoint_path(root, task_id)
    if not path.is_file():
        raise FileNotFoundError(f"No checkpoint: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def append_step(checkpoint: dict[str, Any], step: str) -> None:
    checkpoint.setdefault("completed_steps", []).append(
        {"at": _now_iso(), "step": step}
    )


def record_decision(checkpoint: dict[str, Any], decision: Mapping[str, Any]) -> None:
    entry = {"at": _now_iso(), **dict(decision)}
    checkpoint.setdefault("decisions", []).append(entry)


def record_error(checkpoint: dict[str, Any], message: str, **extra: Any) -> None:
    checkpoint.setdefault("errors", []).append(
        {"at": _now_iso(), "message": message, **extra}
    )


def bump_metric(checkpoint: dict[str, Any], key: str, delta: int = 1) -> None:
    metrics = checkpoint.setdefault("metrics", {})
    metrics[key] = int(metrics.get(key, 0)) + delta


def enforce_budget(checkpoint: Mapping[str, Any]) -> None:
    budget = checkpoint.get("budget") or default_budget()
    metrics = checkpoint.get("metrics") or {}
    started = float(metrics.get("started_at", time.time()))
    elapsed = time.time() - started
    if int(metrics.get("actions", 0)) >= int(budget.get("max_actions", 50)):
        raise BudgetExhausted("max_actions exhausted")
    if int(metrics.get("model_calls", 0)) >= int(budget.get("max_model_calls", 20)):
        raise BudgetExhausted("max_model_calls exhausted")
    if int(metrics.get("retries", 0)) >= int(budget.get("max_retries", 5)):
        raise BudgetExhausted("max_retries exhausted")
    if elapsed > float(budget.get("max_runtime_seconds", 3600)):
        raise BudgetExhausted("max_runtime_seconds exhausted")


def claim_side_effect(checkpoint: dict[str, Any], effect_id: str) -> bool:
    """
    Register a side effect once. Returns True if this call may proceed;
    False if effect_id was already recorded (duplicate / retry).
    """
    seen = checkpoint.setdefault("side_effect_ids", [])
    if effect_id in seen:
        return False
    seen.append(effect_id)
    bump_metric(checkpoint, "actions")
    return True


def outcome_verified(checkpoint: Mapping[str, Any], checks: Mapping[str, bool]) -> bool:
    """All checks must be True before marking done."""
    return all(bool(v) for v in checks.values())
