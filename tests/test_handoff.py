import json
from pathlib import Path

from decision_router.backends.rules import RulesBackend
from decision_router.handoff import enqueue_handoff, resolve_destination
from decision_router.recipes import BRIEFING_NEXT_WORKER
from decision_router.types import ChoiceAnswer, SystemOneResult


def test_low_confidence_falls_back_to_review(tmp_path: Path):
    dest = resolve_destination(
        ChoiceAnswer(choice="write", confidence=0.5),
        allowed={"research", "write", "review"},
        fallback="review",
    )
    assert dest == "review"


def test_enqueue_writes_json(tmp_path: Path):
    b = RulesBackend()
    result = b.system_one(
        {"goal": "g", "completed_work": "Nothing yet."},
        {"next_worker": BRIEFING_NEXT_WORKER},
    )
    job = enqueue_handoff(tmp_path, {"goal": "g", "completed_work": "Nothing yet."}, result)
    data = json.loads(job.read_text())
    assert data["status"] == "queued"
    assert job.parent.name in {"research", "write", "review"}
