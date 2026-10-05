from decision_router.backends.rules import RulesBackend
from decision_router.recipes import BRIEFING_NEXT_WORKER, ENGAGE_ACTION, SAFE_TO_ENGAGE


def test_briefing_empty_work_routes_research():
    b = RulesBackend()
    r = b.system_one(
        {"goal": "Summarize Jev playbook", "completed_work": "Nothing yet."},
        {"next_worker": BRIEFING_NEXT_WORKER},
    )
    assert r.choices["next_worker"].choice == "research"
    assert r.choices["next_worker"].confidence >= 0.85


def test_briefing_rich_work_routes_write():
    work = "url: a url: b source collected " + ("word " * 50)
    b = RulesBackend()
    r = b.system_one(
        {"goal": "Briefing", "completed_work": work},
        {"next_worker": BRIEFING_NEXT_WORKER},
    )
    assert r.choices["next_worker"].choice in {"write", "review"}


def test_engage_slop_skips():
    b = RulesBackend()
    r = b.system_one(
        {
            "post_text": "10 AI tools that will change everything AI tool stack",
            "views": 99999,
            "watchlist": True,
            "floor_views": 5000,
        },
        {"engage_action": ENGAGE_ACTION, "safe_to_engage_without_human": SAFE_TO_ENGAGE},
    )
    assert r.choices["engage_action"].choice == "skip"
    assert r.nouls["safe_to_engage_without_human"].value is False
