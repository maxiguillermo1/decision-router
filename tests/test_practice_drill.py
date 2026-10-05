from decision_router.backends.rules import RulesBackend
from decision_router.practice_drill import SCENARIOS, drill_title, pick_scenario
from decision_router.recipes import GITHUB_ISSUE_ROUTE
from decision_router.handoff import resolve_destination
from decision_router.types import DEFAULT_CONFIDENCE_FLOOR


def _route_issue(state: dict) -> str:
    b = RulesBackend()
    r = b.system_one(state, {"github_issue_route": GITHUB_ISSUE_ROUTE})
    answer = r.choices["github_issue_route"]
    return resolve_destination(
        answer,
        allowed={"triage", "human", "security", "ignore"},
        confidence_floor=DEFAULT_CONFIDENCE_FLOOR,
        fallback="triage",
    )


def test_drill_scenarios_match_expected_routes():
    for key, scenario in SCENARIOS.items():
        state = {
            "title": drill_title(scenario),
            "body_excerpt": scenario.body,
            "labels": ["lab-drill"],
            "author_association": "none",
        }
        dest = _route_issue(state)
        assert dest == scenario.expected_destination, key


def test_pick_scenario_random_is_valid():
    assert pick_scenario("security").key == "security"
