from decision_router.label_policy import label_applied_note, should_apply_routing_label


def test_apply_when_safe_true_and_choice_meets_floor():
    payload = {
        "confidence": 0.86,
        "label": "router-human",
        "safe_auto_label": {"value": True, "confidence": 0.82},
    }
    assert should_apply_routing_label(payload, 0.85) is True
    assert label_applied_note(payload, 0.85) == "yes"


def test_skip_when_choice_below_floor_even_if_safe_true():
    payload = {
        "confidence": 0.84,
        "label": "router-human",
        "safe_auto_label": {"value": True, "confidence": 0.9},
    }
    assert should_apply_routing_label(payload, 0.85) is False


def test_skip_when_safe_false():
    payload = {
        "confidence": 0.9,
        "label": "router-security",
        "safe_auto_label": {"value": False, "confidence": 0.9},
    }
    assert should_apply_routing_label(payload, 0.85) is False
