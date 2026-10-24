#!/usr/bin/env python3
"""发布前敏感信息检查（零第三方依赖）。

【为什么需要这个脚本？】
很多密钥泄露不是因为代码里写了 Key，而是因为：
    - 本地 .env 被误提交；
    - 报告/日志/截图把 Key 带进了仓库；
    - 换了新电脑后，又复制了一份带 Key 的配置。

这个脚本会：
    1. 检查项目根目录有没有不该出现的 .env；
    2. 找出本机 .env / 环境变量里的真实 API Key，并在项目文件里逐字节比对；
    3. 扫描常见的 Key 格式（OpenAI/DeepSeek、智谱、AWS、GitHub、Google、私钥）；
    4. 只输出"哪个文件、哪一行、什么类型"，绝不打印密钥内容。

用法（在项目目录下）：
    python check_secrets.py

退出码：
    0 = 没发现问题
    1 = 发现了需要处理的内容（不会自动删除，避免误伤）
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 这些目录不参与扫描：依赖、缓存、运行时克隆下来的第三方代码。
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    "data",  # 运行时数据，已被 .gitignore 忽略；发布前也可以直接删除
}

TEXT_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx",
    ".html", ".css", ".scss", ".md", ".txt", ".json", ".toml", ".yaml",
    ".yml", ".xml", ".ini", ".cfg", ".conf", ".ps1", ".bat", ".sh",
    ".example", ".gitignore", ".gitattributes", ".env", ".properties",
}

# 这些只是"看起来像"，用于兜底扫描；真正的 Key 优先用本机 .env 精确比对。
KEY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("OpenAI / DeepSeek 风格 Key", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("智谱 GLM 风格 Key", re.compile(r"\b[0-9a-f]{32}\.[A-Za-z0-9]{8,}\b")),
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub Token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("Google API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("私钥文件内容", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

# 这些占位符不算泄露，避免 .env.example 和 README 误报。
PLACEHOLDER_MARKERS = ("your", "xxxx", "填", "在此", "示例", "example")


def parse_env_file(path: Path) -> dict[str, str]:
    """解析简单的 KEY=VALUE 格式的 .env（不依赖 python-dotenv）。"""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return values
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("'\"")
        if not name or not value:
            continue
        if any(marker in value.lower() for marker in PLACEHOLDER_MARKERS):
            continue
        values[name] = value
    return values


def collect_real_secrets() -> dict[str, str]:
    """收集用于精确比对的真实密钥（只比对，不打印）。"""
    secrets: dict[str, str] = {}

    for env_file in (ROOT / ".env", ROOT.parent / ".env"):
        for name, value in parse_env_file(env_file).items():
            if name.endswith("_API_KEY") or name in {"LANGCHAIN_API_KEY", "TAVILY_API_KEY"}:
                secrets[f"{env_file.name}:{name}"] = value

    for name, value in os.environ.items():
        if name.endswith("_API_KEY") and value and len(value) >= 8:
            secrets[f"环境变量:{name}"] = value

    return {label: value for label, value in secrets.items() if len(value) >= 8}


def git_tracks(path: Path) -> bool:
    """如果项目已经是 Git 仓库，判断某个文件是否被跟踪。"""
    if not (ROOT / ".git").exists():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", str(path.relative_to(ROOT))],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    name = path.name.lower()
    return name in {".gitignore", ".gitattributes", "makefile", "dockerfile", "procfile"} or name.startswith("dockerfile.")


def iter_project_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIP_DIRS and not name.startswith(".chrome-")
        ]
        for filename in filenames:
            # 本地 .env 是正常的开发配置（已被 .gitignore 忽略），不扫描它的内容；
            # 但下面会检查它是否被 Git 跟踪。.env.example 仍然要扫描。
            lowered = filename.lower()
            if lowered == ".env" or (lowered.startswith(".env.") and lowered != ".env.example"):
                continue
            yield Path(dirpath) / filename


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def main() -> int:
    real_secrets = collect_real_secrets()
    findings: list[tuple[str, int, str]] = []
    scanned = 0
    project_env = ROOT / ".env"
    env_note = ""
    if project_env.exists():
        if git_tracks(project_env):
            findings.append((".env", 0, "本地 .env 已被 Git 跟踪"))
        else:
            env_note = "检测到本地 .env（已跳过内容扫描）。请确认没有用 git add -f 把它加入暂存区。"

    for path in iter_project_files():
        try:
            if path.stat().st_size > 5_000_000:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        scanned += 1
        rel = str(path.relative_to(ROOT))

        # 1) 真实 Key 逐字节比对（包括图片元数据等二进制文件）
        for label, secret in real_secrets.items():
            if secret.encode("utf-8", errors="ignore") in data:
                text = data.decode("utf-8", errors="ignore")
                findings.append((rel, line_number(text, text.find(secret)), f"真实密钥（{label}）"))

        # 2) 常见 Key 格式扫描（只扫文本文件）
        if not is_text_file(path):
            continue
        text = data.decode("utf-8", errors="ignore")
        for label, pattern in KEY_PATTERNS:
            for match in pattern.finditer(text):
                findings.append((rel, line_number(text, match.start()), label))

    # 去重并稳定排序
    findings = sorted(set(findings), key=lambda item: (item[0], item[1], item[2]))

    print("=" * 64)
    print(" RepoLens 发布前敏感信息检查")
    print("=" * 64)
    print(f"扫描文件：{scanned}")
    print(f"用于精确比对的真实 Key：{len(real_secrets)} 个（只比对，不显示）")
    if env_note:
        print(f"提示：{env_note}")
    print()

    if not findings:
        print("✅ 未发现 API Key / 私钥；项目内没有不应提交的 .env。")
        print()
        print("提醒：")
        print("  1. 图片（screenshots）里的文字无法被本脚本识别，发布截图前请人工确认；")
        print("  2. 不要用 git add -f 提交 .env 或 data/；")
        print("  3. 如果 Key 曾经出现在提交历史里，仅删除当前文件是不够的，需要轮换 Key 并清理历史。")
        return 0

    print("⚠ 发现以下需要处理的内容（未显示密钥原文）：")
    for rel, line, label in findings[:80]:
        location = f"{rel}:{line}" if line else rel
        print(f"  - {location}  [{label}]")
    if len(findings) > 80:
        print(f"  … 还有 {len(findings) - 80} 条")
    print()
    print("处理建议：")
    print("  1. 从项目中删除 .env / 含密钥的文件，把 Key 放到项目外或环境变量；")
    print("  2. 检查 git status，确认没有把 data/、日志、截图临时文件加入暂存区；")
    print("  3. 如果 Key 已经提交过，请立刻在供应商控制台轮换（revoke），再清理 Git 历史。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
