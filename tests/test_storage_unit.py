from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repolens.storage import DB_SCHEMA_VERSION

from tests.support import make_store


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = make_store(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_run_lifecycle_and_events(self):
        self.assertTrue(self.store.available)
        self.assertTrue(self.store.upsert_run("run-1", "examples/demo_shop", "local", model="test-model"))
        self.assertEqual(self.store.get_run("run-1")["status"], "running")
        self.assertTrue(self.store.update_run("run-1", status="done", report_ready=True, repo_name="demo_shop"))
        row = self.store.get_run("run-1")
        self.assertEqual(row["status"], "done")
        self.assertEqual(row["report_ready"], 1)
        self.assertEqual(row["repo_name"], "demo_shop")

        self.store.append_event("run-1", {"seq": 0, "type": "started", "data": {"source": "demo"}, "ts": 1.0})
        self.store.append_event("run-1", {"seq": 1, "type": "done", "data": {"ok": True}, "ts": 2.0})
        events = self.store.events("run-1")
        self.assertEqual([event["type"] for event in events], ["started", "done"])
        self.assertEqual([event["seq"] for event in self.store.events("run-1", from_seq=1)], [1])

        self.assertTrue(self.store.add_message("run-1", "user", "用了什么缓存？"))
        self.assertTrue(self.store.add_message("run-1", "assistant", "Redis", {"model": "test"}))
        messages = self.store.messages("run-1")
        self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
        self.assertEqual(messages[1]["meta"]["model"], "test")

    def test_event_pruning(self):
        for seq in range(5):
            self.store.append_event(
                "run-prune",
                {"seq": seq, "type": "ping", "data": {}, "ts": float(seq)},
                max_events=3,
            )
        events = self.store.events("run-prune")
        self.assertEqual(len(events), 3)
        self.assertEqual(events[-1]["seq"], 4)

    def test_report_index(self):
        report = {
            "schema_version": 2,
            "run_id": "run-2",
            "repo_name": "demo",
            "source": "examples/demo",
            "source_type": "local",
            "generated_at": "2026-01-01T00:00:00+08:00",
            "techs": [{"name": "FastAPI"}],
            "stats": {"code_file_count": 3, "total_loc": 100},
            "ai": {"used": False},
        }
        self.assertTrue(self.store.save_report(report))
        self.assertEqual(self.store.load_report("run-2"), report)
        history = self.store.list_reports()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["run_id"], "run-2")
        self.assertEqual(history[0]["tech_count"], 1)
        self.assertEqual(history[0]["schema_version"], 2)
        self.assertEqual(self.store.stats()["reports"], 1)

    def test_stale_running_is_marked(self):
        self.assertTrue(self.store.upsert_run("run-stale", "x", "local", status="running"))
        self.store.mark_stale_runs()
        self.assertEqual(self.store.get_run("run-stale")["status"], "error")

    def test_schema_version_constant(self):
        self.assertGreaterEqual(DB_SCHEMA_VERSION, 1)
