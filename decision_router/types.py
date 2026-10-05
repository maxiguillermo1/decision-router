"""Structured decision types — Jev-compatible shape for branching in code."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence


@dataclass(frozen=True)
class ChoiceQuestion:
    instructions: str
    criteria: Mapping[str, str]


@dataclass(frozen=True)
class ScoreQuestion:
    instructions: str
    labels: Sequence[str]


@dataclass(frozen=True)
class NoulQuestion:
    instructions: str


Question = ChoiceQuestion | ScoreQuestion | NoulQuestion


@dataclass(frozen=True)
class ChoiceAnswer:
    choice: str
    confidence: float


@dataclass(frozen=True)
class ScoreAnswer:
    label: str
    confidence: float


@dataclass(frozen=True)
class NoulAnswer:
    value: bool
    confidence: float


@dataclass
class SystemOneResult:
    choices: dict[str, ChoiceAnswer] = field(default_factory=dict)
    scores: dict[str, ScoreAnswer] = field(default_factory=dict)
    nouls: dict[str, NoulAnswer] = field(default_factory=dict)
    backend: str = "unknown"
    raw: dict[str, Any] | None = None


DEFAULT_CONFIDENCE_FLOOR = 0.85
