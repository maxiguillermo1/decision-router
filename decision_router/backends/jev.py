"""TypeSafe Jev backend — optional; requires typesafe-sdk and TYPESAFE_API_KEY."""

from __future__ import annotations

import os
from typing import Any, Mapping

from decision_router.backends.base import DecisionBackend
from decision_router.types import (
    ChoiceQuestion,
    NoulQuestion,
    Question,
    ScoreQuestion,
    SystemOneResult,
    ChoiceAnswer,
    ScoreAnswer,
    NoulAnswer,
)


class JevBackend(DecisionBackend):
    def __init__(self, model: str = "jev-1.13.0") -> None:
        self.model = model
        if not os.environ.get("TYPESAFE_API_KEY"):
            raise RuntimeError(
                "TYPESAFE_API_KEY is not set. Use rules backend or add a key."
            )
        try:
            from typesafe_sdk import Choice, Noul, Score, TypeSafeClient  # noqa: F401
        except ImportError as e:
            raise RuntimeError(
                "Install optional dependency: pip install 'decision-router[jev]'"
            ) from e
        self._Choice = Choice
        self._Score = Score
        self._Noul = Noul
        self._client_cls = TypeSafeClient

    def system_one(
        self,
        state: Mapping[str, Any],
        questions: Mapping[str, Question],
    ) -> SystemOneResult:
        sdk_questions: dict[str, Any] = {}
        for name, q in questions.items():
            if isinstance(q, ChoiceQuestion):
                sdk_questions[name] = self._Choice(
                    instructions=q.instructions,
                    criteria=dict(q.criteria),
                )
            elif isinstance(q, ScoreQuestion):
                sdk_questions[name] = self._Score(
                    instructions=q.instructions,
                    labels=list(q.labels),
                )
            elif isinstance(q, NoulQuestion):
                sdk_questions[name] = self._Noul(instructions=q.instructions)

        with self._client_cls(model=self.model) as client:
            raw = client.system_one(state=dict(state), questions=sdk_questions)

        result = SystemOneResult(backend=f"jev:{self.model}", raw={})
        for name in questions:
            if name in getattr(raw, "choices", {}):
                a = raw.choices[name]
                result.choices[name] = ChoiceAnswer(
                    choice=a.choice, confidence=float(a.confidence)
                )
            if name in getattr(raw, "scores", {}):
                a = raw.scores[name]
                result.scores[name] = ScoreAnswer(
                    label=a.label, confidence=float(a.confidence)
                )
            if name in getattr(raw, "nouls", {}):
                a = raw.nouls[name]
                result.nouls[name] = NoulAnswer(
                    value=bool(a.value), confidence=float(a.confidence)
                )
        return result
