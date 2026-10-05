import json
import time

import pytest

from decision_router.checkpoint import (
    BudgetExhausted,
    atomic_write_json,
    claim_side_effect,
    enforce_budget,
    load_checkpoint,
    new_checkpoint,
    outcome_verified,
    refresh_repo_identity,
    save_checkpoint,
)


def test_atomic_write_and_load(tmp_path):
    root = tmp_path / "cp"
    cp = new_checkpoint(goal="test goal", repo_path=None, task_id="abc123")
    path = save_checkpoint(root, cp)
    assert path.is_file()
    loaded = load_checkpoint(root, "abc123")
    assert loaded["goal"] == "test goal"
    assert loaded["task_id"] == "abc123"


def test_duplicate_side_effect(tmp_path):
    cp = new_checkpoint(goal="x")
    assert claim_side_effect(cp, "post-comment#42") is True
    assert claim_side_effect(cp, "post-comment#42") is False
    assert cp["metrics"]["actions"] == 1


def test_budget_exhausted():
    cp = new_checkpoint(goal="x")
    cp["budget"] = {"max_actions": 1, "max_model_calls": 1, "max_retries": 1, "max_runtime_seconds": 3600}
    cp["metrics"]["actions"] = 1
    with pytest.raises(BudgetExhausted):
        enforce_budget(cp)


def test_outcome_verified():
    assert outcome_verified({}, {"file_exists": True, "tests_pass": True})
    assert not outcome_verified({}, {"file_exists": True, "tests_pass": False})


def test_refresh_git_evidence_on_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    import subprocess

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.com", "-c", "user.name=t", "commit", "--allow-empty", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    cp = new_checkpoint(goal="g", repo_path=repo)
    assert cp["repo_identity"].get("commit")
    refresh_repo_identity(cp, repo)
    assert cp["repo_identity"]["dirty"] is False


def test_runtime_budget():
    cp = new_checkpoint(goal="x")
    cp["budget"]["max_runtime_seconds"] = 0
    cp["metrics"]["started_at"] = time.time() - 10
    with pytest.raises(BudgetExhausted):
        enforce_budget(cp)
