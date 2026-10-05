from decision_router.backends.rules import RulesBackend
from decision_router.recipes import GITHUB_ISSUE_ROUTE, GITHUB_PR_ROUTE


def test_issue_security_route():
    b = RulesBackend()
    r = b.system_one(
        {
            "title": "Possible credential leak in auth",
            "body_excerpt": "We found a secret in logs",
            "labels": [],
        },
        {"github_issue_route": GITHUB_ISSUE_ROUTE},
    )
    assert r.choices["github_issue_route"].choice == "security"


def test_pr_wip_wait_ci():
    b = RulesBackend()
    r = b.system_one(
        {
            "title": "WIP: refactor",
            "body_excerpt": "",
            "draft": True,
            "additions": 10,
            "deletions": 2,
            "changed_files": 1,
        },
        {"github_pr_route": GITHUB_PR_ROUTE},
    )
    assert r.choices["github_pr_route"].choice == "wait_ci"


def test_pr_large_diff_human():
    b = RulesBackend()
    r = b.system_one(
        {
            "title": "Big feature",
            "body_excerpt": "details",
            "draft": False,
            "additions": 900,
            "deletions": 50,
            "changed_files": 30,
        },
        {"github_pr_route": GITHUB_PR_ROUTE},
    )
    assert r.choices["github_pr_route"].choice == "human"
