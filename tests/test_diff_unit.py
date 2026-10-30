from __future__ import annotations

import unittest

from repolens.diff import build_diff


def report(run_id: str, techs: list[dict], risk: list[str] | None = None, graph: dict | None = None) -> dict:
    return {
        "schema_version": 3,
        "run_id": run_id,
        "repo_name": "demo",
        "source": "examples/demo_shop",
        "generated_at": f"2026-01-0{run_id[-1]}T00:00:00+08:00",
        "stats": {"file_count": 10, "code_file_count": 4, "total_loc": 100},
        "techs": techs,
        "module_graph": graph or {"nodes": [], "edges": [], "stats": {}},
        "risks": risk or [],
        "architecture": [],
        "highlights": [],
        "learning_path": [],
        "warnings": [],
    }


class DiffTests(unittest.TestCase):
    def test_same_report_has_no_changes(self):
        data = report(
            "run-1",
            [{"name": "FastAPI", "version": "0.1", "module_count": 2}],
            ["没有测试"],
        )
        diff = build_diff(data, data)
        self.assertFalse(diff["has_changes"])
        self.assertEqual(diff["summary"]["tech_changed"], 0)
        self.assertEqual(diff["modules"]["edges_added_count"], 0)

    def test_tech_and_module_changes(self):
        base = report(
            "run-1",
            [
                {"name": "FastAPI", "version": "0.1", "module_count": 2, "category": "后端框架"},
                {"name": "Redis", "version": "5", "module_count": 1, "category": "缓存与消息"},
            ],
            ["缺少测试"],
            {
                "nodes": [
                    {"id": "a.py", "path": "a.py", "dir": "."},
                    {"id": "b.py", "path": "b.py", "dir": "."},
                ],
                "edges": [{"source": "a.py", "target": "b.py"}],
                "stats": {"node_count": 2, "edge_count": 1},
            },
        )
        target = report(
            "run-2",
            [
                {"name": "FastAPI", "version": "0.2", "module_count": 3, "category": "后端框架"},
                {"name": "React", "version": "18", "module_count": 2, "category": "前端框架"},
            ],
            ["现在有测试"],
            {
                "nodes": [
                    {"id": "b.py", "path": "b.py", "dir": "."},
                    {"id": "c.py", "path": "c.py", "dir": "."},
                ],
                "edges": [{"source": "b.py", "target": "c.py"}],
                "stats": {"node_count": 2, "edge_count": 1},
            },
        )
        diff = build_diff(base, target)
        self.assertTrue(diff["has_changes"])
        self.assertEqual(diff["summary"]["tech_added"], 1)
        self.assertEqual(diff["summary"]["tech_removed"], 1)
        self.assertEqual(diff["summary"]["tech_changed"], 1)
        self.assertEqual(diff["techs"]["added"][0]["name"], "React")
        self.assertEqual(diff["techs"]["removed"][0]["name"], "Redis")
        self.assertIn("version", [item["field"] for item in diff["techs"]["changed"][0]["changes"]])
        self.assertEqual(diff["summary"]["module_edges_added"], 1)
        self.assertEqual(diff["summary"]["module_edges_removed"], 1)
        self.assertEqual(diff["summary"]["risk_added"], 1)
        self.assertEqual(diff["summary"]["risk_removed"], 1)

    def test_architecture_changes_count_as_changes(self):
        base = report("run-1", [])
        target = report("run-2", [])
        target["architecture"] = ["新增了一层缓存"]
        diff = build_diff(base, target)
        self.assertTrue(diff["has_changes"])
        self.assertEqual(diff["text"]["architecture"]["added"][0], "新增了一层缓存")
