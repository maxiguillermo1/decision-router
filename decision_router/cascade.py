"""Moderation cascade: rules first, optional Jev on gray-zone (playbook pattern H)."""

from __future__ import annotations

import os
from typing import Any, Mapping

from decision_router.backends import JevBackend, RulesBackend
from decision_router.types import DEFAULT_CONFIDENCE_FLOOR, Question, SystemOneResult


def system_one_cascade(
    state: Mapping[str, Any],
    questions: Mapping[str, Question],
    choice_key: str,
    *,
    confidence_floor: float = DEFAULT_CONFIDENCE_FLOOR,
) -> tuple[SystemOneResult, dict[str, Any]]:
    """
    Run RulesBackend; if routed choice confidence is below the floor and
    TYPESAFE_API_KEY is set, escalate to Jev. Otherwise keep rules output.
    """
    meta: dict[str, Any] = {
        "primary": "rules",
        "escalated_to_jev": False,
        "gray_zone": False,
    }
    rules = RulesBackend().system_one(state, questions)
    answer = rules.choices.get(choice_key)
    if answer is None:
        return rules, meta

    meta["rules_choice"] = answer.choice
    meta["rules_confidence"] = answer.confidence

    if answer.confidence >= confidence_floor:
        return rules, meta

    meta["gray_zone"] = True
    if not os.environ.get("TYPESAFE_API_KEY", "").strip():
        return rules, meta

    try:
        jev = JevBackend().system_one(state, questions)
    except (RuntimeError, OSError, ImportError) as err:
        meta["jev_error"] = str(err)
        return rules, meta

    meta["escalated_to_jev"] = True
    meta["primary"] = "jev"
    return jev, meta
