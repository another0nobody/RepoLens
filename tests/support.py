from __future__ import annotations

from pathlib import Path

from repolens import config
from repolens.context import AnalysisContext
from repolens.events import EventBus
from repolens.report import build_report
from repolens.scanner import scan_repository
from repolens.storage import SQLiteStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_REPO = PROJECT_ROOT / "examples" / "demo_shop"


def demo_snapshot():
    return scan_repository(DEMO_REPO, "examples/demo_shop", "local")


def demo_report():
    snapshot = demo_snapshot()
    bus = EventBus("test-run")
    ctx = AnalysisContext(
        run_id="test-run",
        source="examples/demo_shop",
        source_type="local",
        bus=bus,
    )
    ctx.snapshot = snapshot
    return build_report(ctx)


def make_store(tmp_path: Path) -> SQLiteStore:
    return SQLiteStore(tmp_path / "repolens-test.db")


def with_reports_dir(tmp_path: Path):
    """临时切换报告目录，返回原值，便于测试后恢复。"""
    original = config.REPORTS_DIR
    config.REPORTS_DIR = tmp_path / "reports"
    return original
