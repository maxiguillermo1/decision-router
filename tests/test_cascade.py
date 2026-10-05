import os

from decision_router.cascade import system_one_cascade
from decision_router.recipes import GITHUB_ISSUE_ROUTE


def test_cascade_keeps_rules_when_confident():
    state = {
        "title": "[lab-drill] credential exposure in auth callback",
        "body_excerpt": "credential leak auth bypass",
        "labels": ["lab-drill"],
    }
    result, meta = system_one_cascade(
        state,
        {"github_issue_route": GITHUB_ISSUE_ROUTE},
        "github_issue_route",
        confidence_floor=0.85,
    )
    assert meta["primary"] == "rules"
    assert meta.get("escalated_to_jev") is False
    assert result.choices["github_issue_route"].confidence >= 0.85


def test_cascade_gray_zone_without_key_stays_rules():
    state = {
        "title": "[lab-drill] question",
        "body_excerpt": "How does the confidence floor work?",
        "labels": ["lab-drill"],
    }
    env = os.environ.pop("TYPESAFE_API_KEY", None)
    try:
        result, meta = system_one_cascade(
            state,
            {"github_issue_route": GITHUB_ISSUE_ROUTE},
            "github_issue_route",
            confidence_floor=0.85,
        )
    finally:
        if env is not None:
            os.environ["TYPESAFE_API_KEY"] = env

    assert meta["gray_zone"] is True
    assert meta["primary"] == "rules"
    assert result.choices["github_issue_route"].confidence < 0.85
