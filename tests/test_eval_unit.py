from __future__ import annotations

import unittest
from pathlib import Path

from evals.harness import evaluate_snapshot, load_cases, render_markdown, run_cases
from repolens.scanner import scan_repository

ROOT = Path(__file__).resolve().parent.parent


class EvalHarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = load_cases(ROOT / "evals" / "cases.json")
        cls.case = next(item for item in cls.cases if item["id"] == "node_api")
        cls.snapshot = scan_repository(ROOT / "evals" / "fixtures" / "node_api", "node_api", "eval")

    def test_fixture_meets_expected_facts(self):
        result = evaluate_snapshot(self.snapshot, self.case)
        self.assertTrue(result["passed"])
        self.assertEqual(result["metrics"]["tech_recall"], 1.0)
        self.assertEqual(result["missing_entry_points"], [])
        self.assertIn("src/server.js", self.snapshot.entry_points)

    def test_missing_tech_fails(self):
        case = {"expected": {"techs": ["NoSuchTech"], "min_files": 1}}
        result = evaluate_snapshot(self.snapshot, case)
        self.assertFalse(result["passed"])
        self.assertEqual(result["missing_techs"], ["NoSuchTech"])
        self.assertEqual(result["metrics"]["tech_recall"], 0.0)

    def test_run_cases_and_markdown(self):
        result = run_cases([self.case], ROOT)
        self.assertEqual(result["summary"]["passed"], 1)
        markdown = render_markdown(result)
        self.assertIn("node_api", markdown)
        self.assertIn("通过", markdown)

    def test_missing_directory_is_isolated(self):
        result = run_cases([{"id": "missing", "path": "does-not-exist"}], ROOT)
        self.assertEqual(result["summary"]["failed"], 1)
        self.assertIn("目录不存在", result["cases"][0]["error"])
