"""运行 RepoLens 确定性评测。

用法：

    python scripts/evaluate.py
    python scripts/evaluate.py --case demo_shop --out evals/demo.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evals.harness import load_cases, render_markdown, run_cases  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="RepoLens 多仓库扫描评测")
    parser.add_argument("--cases", default="evals/cases.json", help="用例清单")
    parser.add_argument("--out", default="", help="JSON 输出路径；留空不写文件")
    parser.add_argument("--md", default="", help="Markdown 输出路径；留空不写文件")
    parser.add_argument("--case", default="", help="只跑指定 id")
    parser.add_argument("--base", default=str(PROJECT_ROOT), help="用例路径的基准目录")
    args = parser.parse_args()

    cases_path = (PROJECT_ROOT / args.cases).resolve()
    try:
        cases = load_cases(cases_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"读取用例失败：{exc}")
        return 2
    if args.case:
        cases = [case for case in cases if case.get("id") == args.case]
        if not cases:
            print(f"没有找到用例：{args.case}")
            return 2

    result = run_cases(cases, Path(args.base).resolve())
    markdown = render_markdown(result)
    print(markdown)

    if args.out:
        out = (PROJECT_ROOT / args.out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.md:
        md = (PROJECT_ROOT / args.md).resolve()
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(markdown + "\n", encoding="utf-8")

    summary = result["summary"]
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
