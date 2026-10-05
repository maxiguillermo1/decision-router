"""Synthetic GitHub issues that exercise the full route → agent loop."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class DrillScenario:
    key: str
    title_suffix: str
    body: str
    expected_destination: str


SCENARIOS: dict[str, DrillScenario] = {
    "security": DrillScenario(
        key="security",
        title_suffix="credential exposure in auth callback",
        body=(
            "Automated lab drill — not a real incident.\n\n"
            "Report: possible **credential** leak and **auth bypass** in the OAuth callback path.\n"
            "Please route to security triage."
        ),
        expected_destination="security",
    ),
    "bug": DrillScenario(
        key="bug",
        title_suffix="regression: chief queue jobs not consumed",
        body=(
            "Automated lab drill.\n\n"
            "Steps: run chief.py, open queue/research — job stays queued.\n"
            "**Regression** / **broken** after last deploy."
        ),
        expected_destination="human",
    ),
    "spam": DrillScenario(
        key="spam",
        title_suffix="promo",
        body=(
            "Automated lab drill.\n\n"
            "**Crypto giveaway** — claim your tokens now! WhatsApp me for SEO services."
        ),
        expected_destination="ignore",
    ),
    "triage": DrillScenario(
        key="triage",
        title_suffix="question",
        body="Automated lab drill.\n\nHow does the confidence floor interact with `safe_auto_label`?",
        expected_destination="triage",
    ),
}

DRILL_TITLE_PREFIX = "[lab-drill]"


def pick_scenario(name: str) -> DrillScenario:
    if name == "random":
        return random.choice(list(SCENARIOS.values()))
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")
    return SCENARIOS[name]


def drill_title(scenario: DrillScenario) -> str:
    return f"{DRILL_TITLE_PREFIX} {scenario.title_suffix}"


def is_lab_drill_title(title: str) -> bool:
    return str(title or "").startswith(DRILL_TITLE_PREFIX)
