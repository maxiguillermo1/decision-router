"""When automation may add router labels (choice confidence + safe_auto noul)."""

from __future__ import annotations

from typing import Any, Mapping


def should_apply_routing_label(
    payload: Mapping[str, Any],
    confidence_floor: float,
) -> bool:
    """Apply label when safe_auto is true and the routed *choice* clears the floor."""
    safe = payload.get("safe_auto_label") or {}
    if not safe.get("value"):
        return False
    choice_conf = float(payload.get("confidence") or 0)
    return choice_conf >= confidence_floor


def label_applied_note(payload: Mapping[str, Any], confidence_floor: float) -> str:
    label = payload.get("label")
    if not label:
        return "n/a"
    if should_apply_routing_label(payload, confidence_floor):
        return "yes"
    return "no (confidence or safe_auto_label gate)"
