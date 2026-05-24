import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import main  # noqa: E402


class ScanJobsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)
        if hasattr(main, "SCAN_JOBS"):
            main.SCAN_JOBS.clear()

    def tearDown(self):
        if hasattr(main, "SCAN_JOBS"):
            main.SCAN_JOBS.clear()

    def test_scan_job_lifecycle_exposes_real_progress(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            target_dir = storage_dir / "target"
            target_dir.mkdir()
            (target_dir / "demo.py").write_text("print('hi')\n", encoding="utf-8")
            sbom_file = storage_dir / "sbom.json"
            sbom_file.write_text('{"components": []}', encoding="utf-8")

            def fake_generate(_raw_path: str):
                time.sleep(0.05)
                return str(sbom_file), 3, None

            def fake_semgrep(_target_path: str):
                time.sleep(0.05)
                return [
                    {
                        "file": "demo.py",
                        "line": 1,
                        "rule_id": "demo.rule",
                        "severity": "WARNING",
                        "message": "demo finding",
                        "content": "print('hi')",
                    }
                ]

            def fake_match(_sbom_path: str):
                time.sleep(0.05)
                return {
                    "summary": {"critical": 0, "high": 0, "medium": 1, "low": 0, "total": 1},
                    "details": [
                        {
                            "component": "demo-lib",
                            "version": "1.0.0",
                            "cve_id": "CVE-2026-0001",
                            "severity": "MEDIUM",
                            "cvss_score": 5.0,
                            "cvss_vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N",
                            "source": "NVD",
                            "fix_versions": ["1.0.1"],
                            "description": "demo vuln",
                        }
                    ],
                }

            with (
                patch.object(main, "STORAGE_DIR", storage_dir),
                patch.object(main, "count_files", return_value=1),
                patch.object(main, "generate_sbom", side_effect=fake_generate),
                patch.object(main, "semgrep_analysis", side_effect=fake_semgrep),
                patch.object(main, "match_vulnerabilities", side_effect=fake_match),
                patch.object(main, "get_fix_suggestion", return_value="fix suggestion"),
            ):
                response = self.client.post("/api/scan-jobs", json={"path": str(target_dir)})
                self.assertEqual(response.status_code, 200)
                created = response.json()
                self.assertIn("job_id", created)

                job_id = created["job_id"]
                seen_running = False
                seen_phases = set()
                snapshot = created

                for _ in range(80):
                    snapshot = self.client.get(f"/api/scan-jobs/{job_id}").json()
                    seen_phases.add(snapshot["phase"])
                    if snapshot["status"] == "running":
                        seen_running = True
                    if snapshot["status"] == "completed":
                        break
                    time.sleep(0.02)

                self.assertTrue(seen_running)
                self.assertIn("SBOM", seen_phases)
                self.assertIn("SAST", seen_phases)
                self.assertIn("CVE", seen_phases)
                self.assertEqual(snapshot["status"], "completed")
                self.assertEqual(snapshot["percent"], 100)
                self.assertEqual(snapshot["report"]["scan_info"]["component_count"], 3)
                self.assertEqual(snapshot["stages"][-1]["status"], "completed")
                self.assertTrue(snapshot["report_id"].startswith("scan_"))

    def test_scan_job_status_returns_404_for_unknown_job(self):
        response = self.client.get("/api/scan-jobs/job-missing")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
