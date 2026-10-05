"""Deterministic System One — no API cost; use for crisp menus and tests."""

from __future__ import annotations

import re
from typing import Any, Mapping

from decision_router.backends.base import DecisionBackend
from decision_router.github_event import looks_security, looks_spam, looks_wip, text_blob
from decision_router.practice_drill import is_lab_drill_title
from decision_router.types import (
    ChoiceAnswer,
    ChoiceQuestion,
    NoulAnswer,
    NoulQuestion,
    Question,
    ScoreAnswer,
    ScoreQuestion,
    SystemOneResult,
)

_SOURCE_HINT = re.compile(
    r"\b(url|http|source|cite|paper|article|fetched|collected)\b",
    re.I,
)
_DRAFT_HINT = re.compile(r"\b(draft|wrote|written|outline|summary)\b", re.I)


class RulesBackend(DecisionBackend):
    """Heuristic router aligned with briefing + engage-gate recipes."""

    def system_one(
        self,
        state: Mapping[str, Any],
        questions: Mapping[str, Question],
    ) -> SystemOneResult:
        result = SystemOneResult(backend="rules")
        for name, question in questions.items():
            if isinstance(question, ChoiceQuestion):
                result.choices[name] = self._choice(state, question, name)
            elif isinstance(question, ScoreQuestion):
                result.scores[name] = self._score(state, question, name)
            elif isinstance(question, NoulQuestion):
                result.nouls[name] = self._noul(state, question, name)
        return result

    def _choice(
        self, state: Mapping[str, Any], q: ChoiceQuestion, key: str
    ) -> ChoiceAnswer:
        options = list(q.criteria.keys())
        if key == "next_worker":
            return self._briefing_next_worker(state, options)
        if key == "engage_action":
            return self._engage_action(state, options)
        if key == "github_issue_route":
            return self._github_issue_route(state, options)
        if key == "github_pr_route":
            return self._github_pr_route(state, options)
        return ChoiceAnswer(choice=options[-1], confidence=0.5)

    def _briefing_next_worker(
        self, state: Mapping[str, Any], options: list[str]
    ) -> ChoiceAnswer:
        goal = str(state.get("goal") or "").strip()
        work = str(state.get("completed_work") or "").strip()
        if not goal:
            return ChoiceAnswer(choice=_pick(options, "review", "write", "research"), confidence=0.9)
        if not work or work.lower() in {"nothing yet.", "nothing yet", "none"}:
            return ChoiceAnswer(choice=_pick(options, "research"), confidence=0.88)
        source_signals = len(_SOURCE_HINT.findall(work))
        word_count = len(work.split())
        if source_signals >= 2 or word_count >= 120:
            if _DRAFT_HINT.search(work):
                return ChoiceAnswer(choice=_pick(options, "review"), confidence=0.86)
            return ChoiceAnswer(choice=_pick(options, "write"), confidence=0.87)
        if word_count >= 40 or source_signals >= 1:
            return ChoiceAnswer(
                choice=_pick(options, "write", "research"),
                confidence=0.72,
            )
        return ChoiceAnswer(choice=_pick(options, "research"), confidence=0.84)

    def _engage_action(
        self, state: Mapping[str, Any], options: list[str]
    ) -> ChoiceAnswer:
        views = int(state.get("views") or 0)
        floor = int(state.get("floor_views") or 5000)
        watchlist = bool(state.get("watchlist"))
        text = str(state.get("post_text") or "")
        slop = len(text) > 20 and text.lower().count("ai tool") >= 2
        if slop or (not watchlist and views < floor):
            return ChoiceAnswer(choice=_pick(options, "skip"), confidence=0.91)
        if watchlist and views >= floor * 2:
            return ChoiceAnswer(
                choice=_pick(options, "draft_full", "draft_short", "escalate_human"),
                confidence=0.8,
            )
        if watchlist and views >= floor:
            return ChoiceAnswer(choice=_pick(options, "draft_short"), confidence=0.78)
        return ChoiceAnswer(choice=_pick(options, "skip"), confidence=0.85)

    def _score(
        self, state: Mapping[str, Any], q: ScoreQuestion, key: str
    ) -> ScoreAnswer:
        labels = list(q.labels)
        if key == "urgency":
            text = f"{state.get('goal', '')} {state.get('completed_work', '')}".lower()
            if any(w in text for w in ("asap", "urgent", "today", "deadline")):
                return ScoreAnswer(label=labels[-1], confidence=0.82)
            if any(w in text for w in ("soon", "this week")):
                return ScoreAnswer(label=labels[max(1, len(labels) // 2)], confidence=0.75)
            return ScoreAnswer(label=labels[0], confidence=0.8)
        if key == "github_urgency":
            return self._github_urgency(state, labels)
        mid = labels[len(labels) // 2]
        return ScoreAnswer(label=mid, confidence=0.6)

    def _noul(
        self, state: Mapping[str, Any], q: NoulQuestion, key: str
    ) -> NoulAnswer:
        if key == "safe_to_run":
            return NoulAnswer(value=False, confidence=0.95)
        if key == "safe_to_engage_without_human":
            return NoulAnswer(value=False, confidence=0.95)
        if key == "github_safe_auto_label":
            return self._github_safe_auto_label(state)
        return NoulAnswer(value=False, confidence=0.7)

    def _github_issue_route(
        self, state: Mapping[str, Any], options: list[str]
    ) -> ChoiceAnswer:
        if looks_spam(state):
            return ChoiceAnswer(choice=_pick(options, "ignore"), confidence=0.92)
        if looks_security(state):
            return ChoiceAnswer(choice=_pick(options, "security"), confidence=0.9)
        text = text_blob(state)
        if "bug" in text or "regression" in text or "broken" in text:
            return ChoiceAnswer(choice=_pick(options, "human"), confidence=0.86)
        if len(text.strip()) < 25:
            return ChoiceAnswer(choice=_pick(options, "triage"), confidence=0.8)
        if "?" in text and len(text) < 400:
            return ChoiceAnswer(choice=_pick(options, "triage", "human"), confidence=0.74)
        return ChoiceAnswer(choice=_pick(options, "human"), confidence=0.85)

    def _github_pr_route(
        self, state: Mapping[str, Any], options: list[str]
    ) -> ChoiceAnswer:
        if looks_wip(state):
            return ChoiceAnswer(choice=_pick(options, "wait_ci"), confidence=0.9)
        adds = int(state.get("additions") or 0)
        dels = int(state.get("deletions") or 0)
        files = int(state.get("changed_files") or 0)
        if looks_security(state):
            return ChoiceAnswer(choice=_pick(options, "human"), confidence=0.88)
        if files <= 2 and adds + dels < 40:
            title = str(state.get("title") or "").lower()
            if any(w in title for w in ("doc", "readme", "typo", "comment")):
                return ChoiceAnswer(
                    choice=_pick(options, "skip_noise"), confidence=0.87
                )
        if adds + dels > 800 or files > 25:
            return ChoiceAnswer(choice=_pick(options, "human"), confidence=0.84)
        return ChoiceAnswer(choice=_pick(options, "request_review"), confidence=0.86)

    def _github_urgency(self, state: Mapping[str, Any], labels: list[str]) -> ScoreAnswer:
        text = text_blob(state)
        if looks_security(state) or any(
            w in text for w in ("production down", "outage", "sev0", "sev1", "blocker")
        ):
            return ScoreAnswer(label=labels[-1], confidence=0.85)
        if "bug" in text or "urgent" in text:
            return ScoreAnswer(label=labels[max(1, len(labels) - 2)], confidence=0.78)
        return ScoreAnswer(label=labels[0], confidence=0.8)

    def _github_safe_auto_label(self, state: Mapping[str, Any]) -> NoulAnswer:
        if is_lab_drill_title(str(state.get("title") or "")):
            return NoulAnswer(value=True, confidence=0.9)
        if looks_security(state) or looks_spam(state):
            return NoulAnswer(value=False, confidence=0.9)
        assoc = str(state.get("author_association") or "").lower()
        if assoc in {"none", "first_timer", "first_time_contributor"}:
            return NoulAnswer(value=False, confidence=0.75)
        return NoulAnswer(value=True, confidence=0.82)


def _pick(options: list[str], *preferred: str) -> str:
    for p in preferred:
        if p in options:
            return p
    return options[0] if options else "review"
