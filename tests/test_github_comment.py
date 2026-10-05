from decision_router.github_comment import format_route_comment


def test_format_route_comment_includes_destination():
    body = format_route_comment(
        {
            "destination": "human",
            "choice": "human",
            "confidence": 0.91,
            "backend": "rules",
            "label": "router-human",
            "urgency": {"label": "medium", "confidence": 0.8},
            "safe_auto_label": {"value": True, "confidence": 0.9},
        }
    )
    assert "destination" in body
    assert "`human`" in body
    assert "never auto-merge" in body
