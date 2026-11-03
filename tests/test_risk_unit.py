from __future__ import annotations

import unittest

from repolens.risk import build_risk_panel


def report(**overrides):
    data = {
        "run_id": "risk-1",
        "repo_name": "demo",
        "risks": [],
        "warnings": [],
        "stats": {"truncated": False},
        "techs": [],
        "module_graph": {"nodes": [], "edges": [], "stats": {"cycle_count": 0}},
    }
    data.update(overrides)
    return data


class RiskPanelTests(unittest.TestCase):
    def test_aggregates_risks_and_graph_cycles(self):
        data = build_risk_panel(
            report(
                risks=["缺少依赖锁文件"],
                warnings=["扫描被截断"],
                techs=[
                    {"name": "Redis", "category": "缓存与消息", "confidence": "低", "modules": [], "evidence": []},
                    {"name": "FastAPI", "category": "后端框架", "confidence": "高", "modules": [{"path": "main.py"}], "evidence": []},
                ],
                module_graph={
                    "nodes": [{"path": "a.py", "cycle": True}, {"path": "b.py", "cycle": True}],
                    "edges": [],
                    "stats": {"cycle_count": 1},
                },
                stats={"truncated": True},
            )
        )
        titles = [item["title"] for item in data["findings"]]
        self.assertTrue(any("缺少依赖锁" in title for title in titles))
        self.assertTrue(any("循环" in title for title in titles))
        self.assertTrue(any("测试" in title for title in titles))
        self.assertTrue(any("置信度" in title for title in titles))
        self.assertGreater(data["counts"]["high"], 0)
        self.assertGreater(data["score"], 0)

    def test_clean_report_has_no_findings(self):
        data = build_risk_panel(
            report(
                techs=[
                    {"name": "pytest", "category": "测试与质量", "confidence": "高"},
                    {"name": "GitHub Actions", "category": "基础设施与运维", "confidence": "高"},
                ],
            )
        )
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["level"], "none")
        self.assertEqual(data["score"], 0)

    def test_cycle_evidence_is_exposed(self):
        data = build_risk_panel(
            report(
                module_graph={
                    "nodes": [{"path": "a.py", "cycle": True}],
                    "edges": [],
                    "stats": {"cycle_count": 1},
                },
            )
        )
        cycle = next(item for item in data["findings"] if "循环" in item["title"])
        self.assertEqual(cycle["evidence"][0]["path"], "a.py")
