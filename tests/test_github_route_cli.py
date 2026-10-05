import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "issue_opened.json"


def test_github_route_fixture(tmp_path):
    out = tmp_path / "out.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "github_route.py"),
            "--event",
            str(FIXTURE),
            "--no-queue",
            "--output",
            str(out),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(out.read_text())
    assert data["kind"] == "issue"
    assert data["destination"] in {"human", "triage", "security", "ignore"}
