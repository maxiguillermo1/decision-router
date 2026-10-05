from decision_router.backends import DecisionBackend, JevBackend, RulesBackend
from decision_router.types import (
    DEFAULT_CONFIDENCE_FLOOR,
    ChoiceQuestion,
    NoulQuestion,
    ScoreQuestion,
    SystemOneResult,
)

__all__ = [
    "DEFAULT_CONFIDENCE_FLOOR",
    "ChoiceQuestion",
    "NoulQuestion",
    "ScoreQuestion",
    "SystemOneResult",
    "DecisionBackend",
    "JevBackend",
    "RulesBackend",
    "get_backend",
    "system_one",
]


def get_backend(name: str = "rules") -> DecisionBackend:
    if name == "rules":
        return RulesBackend()
    if name in ("jev", "typesafe"):
        return JevBackend()
    raise ValueError(f"Unknown backend: {name}")


def system_one(
    state: dict,
    questions: dict,
    backend: str = "rules",
) -> SystemOneResult:
    return get_backend(backend).system_one(state, questions)
