from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repolens.watch import repo_status


def report(root: Path, generated_at: str) -> dict:
    return {
        "run_id": "watch-1",
        "source_type": "local",
        "local_path": str(root),
        "generated_at": generated_at,
    }


class WatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "app.py").write_text("print('hello')\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_detects_changed_files(self):
        data = repo_status(report(self.root, "2000-01-01T00:00:00+08:00"))
        self.assertTrue(data["available"])
        self.assertTrue(data["changed"])
        self.assertEqual(data["latest_path"], "app.py")
        self.assertGreater(data["files_checked"], 0)

    def test_future_baseline_is_unchanged(self):
        data = repo_status(report(self.root, "2099-01-01T00:00:00+08:00"))
        self.assertTrue(data["available"])
        self.assertFalse(data["changed"])

    def test_github_report_is_not_watchable(self):
        data = repo_status({"source_type": "github", "local_path": str(self.root)})
        self.assertFalse(data["available"])
        self.assertIn("本地", data["reason"])

    def test_missing_directory(self):
        data = repo_status(report(self.root / "missing", "2020-01-01T00:00:00+08:00"))
        self.assertFalse(data["available"])
