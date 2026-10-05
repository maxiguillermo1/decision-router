"""Reusable question sets from the Jev builder playbook."""

from decision_router.types import ChoiceQuestion, NoulQuestion, ScoreQuestion

BRIEFING_NEXT_WORKER = ChoiceQuestion(
    instructions="Choose the next step for a research briefing.",
    criteria={
        "research": "Collect evidence still needed for the goal.",
        "write": "Draft the briefing from sufficient evidence.",
        "review": "Goal unclear, outside scope, or work complete.",
    },
)

BRIEFING_URGENCY = ScoreQuestion(
    instructions="Rate request urgency.",
    labels=["low", "medium", "high", "critical"],
)

SAFE_TO_RUN = NoulQuestion(
    instructions="The requested action is safe to execute without human review.",
)

ENGAGE_ACTION = ChoiceQuestion(
    instructions="How to handle this X post (drafts only — never auto-post).",
    criteria={
        "skip": "Low signal or below attention floor.",
        "draft_short": "Worth a short reply draft into review folder.",
        "draft_full": "Strong fit for a full reply draft.",
        "escalate_human": "Sensitive or high-stakes — human only.",
    },
)

SAFE_TO_ENGAGE = NoulQuestion(
    instructions="Safe to engage on X without human review (default policy: false).",
)

GITHUB_ISSUE_ROUTE = ChoiceQuestion(
    instructions="First-pass route for a new GitHub issue (label + queue only; no auto-close).",
    criteria={
        "triage": "Unclear, needs human classification.",
        "human": "Real work item — team should own it.",
        "security": "Possible vulnerability or sensitive security report.",
        "ignore": "Spam, junk, or bot noise.",
    },
)

GITHUB_PR_ROUTE = ChoiceQuestion(
    instructions="First-pass route for a pull request (never auto-merge).",
    criteria={
        "wait_ci": "Draft/WIP — wait for CI and author signal.",
        "request_review": "Ready for normal review.",
        "human": "Large or sensitive change — senior review.",
        "skip_noise": "Trivial docs-only or negligible diff.",
    },
)

GITHUB_URGENCY = ScoreQuestion(
    instructions="How soon should a human look at this?",
    labels=["low", "medium", "high", "critical"],
)

GITHUB_SAFE_AUTO_LABEL = NoulQuestion(
    instructions="Safe for automation to add routing labels without human approval.",
)
