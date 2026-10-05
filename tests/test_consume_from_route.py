import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_consume_from_route_result(tmp_path):
    job_dir = tmp_path / "queue" / "github" / "triage"
    job_dir.mkdir(parents=True)
    job = job_dir / "abc.json"
    job.write_text(json.dumps({"status": "queued", "title": "x"}), encoding="utf-8")
    route = tmp_path / "route-result.json"
    route.write_text(
        json.dumps(
            {
                "destination": "triage",
                "queue_job": str(job),
                "repo": "o/r",
                "number": 1,
                "kind": "issue",
            }
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "consume_from_route_result.py"),
            str(route),
            "--mark",
            "done",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(job.read_text())
    assert data["status"] == "done"
