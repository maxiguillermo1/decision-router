from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from decision_router.types import Question, SystemOneResult


class DecisionBackend(ABC):
    @abstractmethod
    def system_one(
        self,
        state: Mapping[str, Any],
        questions: Mapping[str, Question],
    ) -> SystemOneResult:
        raise NotImplementedError
