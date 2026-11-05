from __future__ import annotations

import unittest

from repolens.grounding import check_grounding

from tests.support import demo_report


class GroundingTests(unittest.TestCase):
    def setUp(self):
        self.report = demo_report()

    def test_valid_citation(self):
        result = check_grounding(self.report, "入口在 `backend/app/main.py:10`，负责挂载路由。")
        self.assertTrue(result["has_citations"])
        self.assertEqual(result["valid"], 1)
        self.assertEqual(result["invalid"], 0)
        self.assertEqual(result["score"], 100)

    def test_unknown_path(self):
        result = check_grounding(self.report, "核心逻辑在 `backend/app/nope.py:3`。")
        self.assertEqual(result["invalid"], 1)
        self.assertIn("没有这个文件", result["citations"][0]["reason"])

    def test_wrong_line_is_invalid(self):
        result = check_grounding(self.report, "`backend/app/main.py:9999` 是入口。")
        self.assertEqual(result["invalid"], 1)

    def test_path_only_is_valid(self):
        result = check_grounding(self.report, "先看 `backend/app/main.py`。")
        self.assertEqual(result["valid"], 1)
        self.assertEqual(result["score"], 100)

    def test_no_citations(self):
        result = check_grounding(self.report, "这是一个 FastAPI 项目。")
        self.assertFalse(result["has_citations"])
        self.assertEqual(result["score"], 0)

    def test_mixed_citations(self):
        result = check_grounding(
            self.report,
            "入口 `backend/app/main.py:10`，但 `backend/app/nope.py:3` 不存在。",
        )
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["valid"], 1)
        self.assertEqual(result["invalid"], 1)
        self.assertEqual(result["score"], 50)
