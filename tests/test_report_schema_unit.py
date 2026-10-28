from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repolens import config
from repolens.report import (
    REPORT_SCHEMA_VERSION,
    load_report,
    normalize_report,
    save_report,
)

from tests.support import demo_report, make_store


class ReportSchemaTests(unittest.TestCase):
    def test_report_has_schema_and_hierarchy(self):
        report = demo_report()
        self.assertEqual(report["schema_version"], REPORT_SCHEMA_VERSION)
        self.assertTrue(report["techs"])
        for tech in report["techs"]:
            self.assertTrue(tech["function"])
            self.assertTrue(tech["layer"])
            self.assertIsInstance(tech["function_order"], int)
            self.assertIsInstance(tech["layer_order"], int)

        redis = next(tech for tech in report["techs"] if tech["name"] == "Redis")
        self.assertEqual(redis["function"], "提供数据缓存")
        self.assertEqual(redis["layer"], "数据与存储")

    def test_legacy_report_is_normalized(self):
        legacy = {
            "run_id": "legacy-1",
            "repo_name": "legacy",
            "techs": [
                {
                    "key": "redis",
                    "name": "Redis",
                    "category": "缓存与消息",
                    "usage_tags": ["缓存"],
                },
                {
                    "key": "fastapi",
                    "name": "FastAPI",
                    "category": "后端框架",
                },
            ],
        }
        normalized = normalize_report(legacy)
        self.assertEqual(normalized["schema_version"], REPORT_SCHEMA_VERSION)
        by_name = {tech["name"]: tech for tech in normalized["techs"]}
        self.assertEqual(by_name["Redis"]["function"], "提供数据缓存")
        self.assertEqual(by_name["Redis"]["layer"], "数据与存储")
        self.assertEqual(by_name["FastAPI"]["function"], "提供后端接口")
        self.assertEqual(by_name["FastAPI"]["layer"], "后端")
        self.assertEqual(normalized["warnings"], [])

    def test_save_and_load_report_with_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            original = config.REPORTS_DIR
            config.REPORTS_DIR = tmp_path / "reports"
            try:
                report = demo_report()
                store = make_store(tmp_path)
                save_report(report, storage=store)
                loaded = load_report(report["run_id"], storage=store)
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded["schema_version"], REPORT_SCHEMA_VERSION)
                self.assertTrue(loaded["techs"][0]["layer"])
                self.assertIsNotNone(store.load_report(report["run_id"]))
            finally:
                config.REPORTS_DIR = original
