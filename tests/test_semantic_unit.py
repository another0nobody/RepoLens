from __future__ import annotations

import json
import unittest

from repolens.semantic import _parse_results, review

from tests.support import demo_report


class FakeModel:
    def __init__(self, verdict="support"):
        self.verdict = verdict

    def invoke(self, _prompt):
        payload = {
            "results": [
                {
                    "index": 0,
                    "verdict": self.verdict,
                    "reason": "引用行包含入口相关代码",
                    "quote": "from app.db import init_db",
                }
            ]
        }
        return type("Response", (), {"content": json.dumps(payload)})()


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.report = demo_report()
        self.answer = "入口在 `backend/app/main.py:10`。"

    def test_supported(self):
        result = review(self.report, self.answer, model=FakeModel("support"))
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["results"][0]["verdict_label"], "支持")

    def test_partial(self):
        result = review(self.report, self.answer, model=FakeModel("partial"))
        self.assertEqual(result["score"], 50)

    def test_unsupported(self):
        result = review(self.report, self.answer, model=FakeModel("unsupported"))
        self.assertEqual(result["score"], 0)

    def test_no_citations(self):
        from repolens.semantic import SemanticError

        with self.assertRaises(SemanticError):
            review(self.report, "只有文字，没有引用。", model=FakeModel())

    def test_parse_fills_missing_rows(self):
        rows = _parse_results('{"results":[{"index":0,"verdict":"support","reason":"ok"}]}', 2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["verdict"], "partial")
