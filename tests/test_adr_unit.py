from __future__ import annotations

import unittest

from repolens.adr import AdrError, build_adr

from tests.support import demo_report


class AdrTests(unittest.TestCase):
    def setUp(self):
        self.report = demo_report()

    def test_build_redis_adr(self):
        result = build_adr(self.report, "Redis")
        self.assertEqual(result["tech"], "Redis")
        self.assertTrue(result["filename"].endswith(".md"))
        self.assertIn("# ADR：采用 Redis", result["markdown"])
        self.assertIn("提供数据缓存", result["markdown"])
        self.assertIn("## 备选方案", result["markdown"])
        self.assertIn("## 证据", result["markdown"])
        self.assertIn("仓库中没有记录", result["markdown"])
        self.assertTrue(result["alternatives"])

    def test_unknown_tech(self):
        with self.assertRaises(AdrError) as context:
            build_adr(self.report, "NoSuchTech")
        self.assertEqual(context.exception.status, 404)

    def test_filename_is_safe(self):
        result = build_adr(self.report, "Redis")
        self.assertNotIn("/", result["filename"])
        self.assertNotIn("\\", result["filename"])
