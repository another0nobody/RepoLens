from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from repolens.scanner import scan_repository

from tests.support import demo_snapshot


class ScannerTests(unittest.TestCase):
    def test_demo_repo_has_core_facts(self):
        snapshot = demo_snapshot()
        stats = snapshot.to_dict()["stats"]
        self.assertGreater(stats["file_count"], 0)
        self.assertGreater(stats["code_file_count"], 0)
        self.assertGreater(stats["total_loc"], 0)

        names = {tech.name for tech in snapshot.techs}
        self.assertTrue({"FastAPI", "React", "SQLAlchemy", "Redis", "Docker"} <= names)

    def test_scanner_detects_code_usage_beyond_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text(
                'from redis import Redis\n\n'
                'cache = Redis.from_url("redis://localhost:6379/1")\n'
                'cache.set("key", "value")\n',
                encoding="utf-8",
            )
            snapshot = scan_repository(root, str(root), "local")
            redis = next((tech for tech in snapshot.techs if tech.name == "Redis"), None)
            self.assertIsNotNone(redis)
            self.assertIn("缓存", redis.usage_tags)
            self.assertTrue(
                any(item.get("kind") == "usage" for item in redis.evidence) or redis.modules
            )

    def test_scanner_ignores_redis_in_docstring(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.py").write_text(
                '"""这个文件只讨论 Redis，但没有真正使用它。"""\nvalue = 1\n',
                encoding="utf-8",
            )
            snapshot = scan_repository(root, str(root), "local")
            self.assertTrue(all(tech.name != "Redis" for tech in snapshot.techs))
