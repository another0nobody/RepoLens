from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repolens import config
from repolens.server import RepoLensApp

from tests.support import demo_report


class AppPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.original_reports = config.REPORTS_DIR
        config.REPORTS_DIR = self.root / "reports"
        self.app = RepoLensApp(db_path=self.root / "app.db")
        self.report = demo_report()

    def tearDown(self):
        config.REPORTS_DIR = self.original_reports
        self.tmp.cleanup()

    def test_history_merges_sqlite(self):
        self.app.storage.save_report(self.report)
        items = self.app.history()
        self.assertTrue(any(item["run_id"] == self.report["run_id"] for item in items))
        loaded = self.app.get_report(self.report["run_id"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["run_id"], self.report["run_id"])

    def test_ensure_run_restores_chat_history(self):
        self.app.storage.save_report(self.report)
        self.app.storage.add_message(self.report["run_id"], "user", "之前的问题")
        run = self.app.ensure_run_for_report(self.report["run_id"], self.report)
        self.assertEqual(run.ctx.chat_history[0]["content"], "之前的问题")
        self.assertFalse(run.ctx.chat_seeded)
