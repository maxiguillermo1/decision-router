from decision_router.agent_dispatch import (
    AGENT_DESTINATIONS,
    build_template_comment,
    should_spawn_agent,
)


def test_should_spawn_agent_human():
    assert should_spawn_agent({"destination": "human"})
    assert not should_spawn_agent({"destination": "ignore"})
    assert not should_spawn_agent({"destination": "wait_ci"})
    assert "security" in AGENT_DESTINATIONS


def test_template_comment_includes_destination():
    body = build_template_comment(
        {
            "destination": "triage",
            "repo": "o/r",
            "number": 3,
            "kind": "issue",
            "state": {"title": "Help"},
        },
        {"title": "Help", "labels": ["bug"]},
    )
    assert "automated agent" in body
    assert "`triage`" in body
    assert "CURSOR_API_KEY" in body
