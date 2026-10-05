import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_run_agent_template_dry_run(tmp_path):
    job_dir = tmp_path / "queue" / "github" / "human"
    job_dir.mkdir(parents=True)
    job = job_dir / "abc.json"
    job.write_text(json.dumps({"status": "queued"}), encoding="utf-8")
    route = tmp_path / "route-result.json"
    route.write_text(
        json.dumps(
            {
                "destination": "human",
                "queue_job": str(job),
                "repo": "o/r",
                "number": 1,
                "kind": "issue",
                "state": {"title": "Bug report"},
            }
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_agent_from_route.py"),
            str(route),
            "--backend",
            "template",
            "--dry-run",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    summary = json.loads(proc.stdout)
    assert summary.get("backend") == "template"
    assert summary.get("spawned") is True
    assert json.loads(job.read_text())["status"] == "done"
