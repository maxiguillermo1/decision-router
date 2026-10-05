"""Write JSON jobs into queue folders — chief.py pattern from TypeSafe starter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from decision_router.types import (
    DEFAULT_CONFIDENCE_FLOOR,
    ChoiceAnswer,
    SystemOneResult,
)


def resolve_destination(
    answer: ChoiceAnswer,
    *,
    allowed: set[str],
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
    fallback: str = "review",
) -> str:
    if answer.choice in allowed and answer.confidence >= confidence_floor:
        return answer.choice
    return fallback


def enqueue_handoff(
    queue_root: Path,
    state: Mapping[str, Any],
    result: SystemOneResult,
    choice_key: str = "next_worker",
    *,
    allowed_destinations: set[str] | None = None,
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
    fallback: str = "review",
) -> Path:
    answer = result.choices[choice_key]
    allowed = allowed_destinations or {"research", "write", "review"}

    destination = resolve_destination(
        answer,
        allowed=allowed,
        confidence_floor=confidence_floor,
        fallback=fallback,
    )
    folder = queue_root / destination
    folder.mkdir(parents=True, exist_ok=True)
    job = folder / f"{uuid4().hex}.json"
    payload: dict[str, Any] = {
        **dict(state),
        "choice": answer.choice,
        "confidence": answer.confidence,
        "destination": destination,
        "status": "queued",
        "backend": result.backend,
    }
    if result.scores:
        payload["scores"] = {
            k: {"label": v.label, "confidence": v.confidence}
            for k, v in result.scores.items()
        }
    if result.nouls:
        payload["nouls"] = {
            k: {"value": v.value, "confidence": v.confidence}
            for k, v in result.nouls.items()
        }
    job.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return job
