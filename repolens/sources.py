"""把用户输入变成"本地可以扫描的目录"。

支持两种来源：

    1. 本地路径：C:\\code\\my-project 或 ./examples/demo_shop
    2. GitHub 地址：https://github.com/owner/repo 或简写 owner/repo

【给初学者：为什么单独一个文件？】
"拿到仓库"和"分析仓库"是两件不同的事：
    - 拿到仓库要处理网络、git 命令、路径安全；
    - 分析仓库是纯本地的文件扫描。
分开写，Agent 的工具里就只需要说"帮我准备这个来源"，逻辑更清楚。
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from . import config

# 允许的 GitHub 写法：
#   https://github.com/owner/repo
#   http://github.com/owner/repo.git
#   owner/repo
_GITHUB_URL = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
_GITHUB_SHORT = re.compile(r"^(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)$")

# 这些系统目录不应该被当成"代码仓库"扫描（保护措施，防止误操作）。
_FORBIDDEN_LOCAL = {
    "c:\\windows",
    "c:\\program files",
    "c:\\program files (x86)",
    "c:\\programdata",
    "c:\\users",
    "/",
    "/etc",
    "/usr",
    "/bin",
    "/system",
}


class SourceError(Exception):
    """来源有问题时抛出，消息会直接显示给用户。"""


def looks_like_github(source: str) -> bool:
    """判断用户输入的是不是 GitHub 地址。"""
    text = source.strip()
    if _GITHUB_URL.match(text):
        return True
    # 简写 owner/repo 只在明确不像本地路径时才认：
    # 本地路径通常包含盘符、斜杠、反斜杠或点号。
    if "/" in text and "\\" not in text and not text.startswith((".", "/", "~")):
        match = _GITHUB_SHORT.match(text)
        if match and "." not in text.split("/", 1)[0]:
            # 如果本机真的存在 examples/demo_shop 这样的相对路径，优先当成本地路径。
            try:
                candidate = Path(text).expanduser()
                if candidate.exists() or (config.PROJECT_ROOT / candidate).exists():
                    return False
            except OSError:
                pass
            return True
    return False


def parse_github(source: str) -> tuple[str, str]:
    """把 GitHub 地址解析成 (owner, repo)。"""
    text = source.strip()
    match = _GITHUB_URL.match(text) or _GITHUB_SHORT.match(text)
    if not match:
        raise SourceError(
            "GitHub 地址格式不对。正确写法示例：https://github.com/psf/requests "
            "或简写 psf/requests"
        )
    repo = match.group("repo")
    if repo.endswith(".git"):
        repo = repo[:-4]
    return match.group("owner"), repo


def validate_local_path(source: str) -> Path:
    """检查本地路径是否可用，返回绝对路径。

    检查内容：
        - 必须存在、必须是目录；
        - 不能是盘符根目录或 Windows 系统目录；
        - 如果配置了 REPOLENS_ALLOWED_ROOTS，必须在允许范围内。
    """
    raw = source.strip().strip('"').strip("'")
    if not raw:
        raise SourceError("请输入本地仓库路径，或者粘贴一个 GitHub 地址。")

    path = Path(os.path.expandvars(os.path.expanduser(raw)))
    # 相对路径先按"当前工作目录"找；找不到再按"项目根目录"找。
    # 这样无论你从哪个目录启动 run.py，示例路径都能正常工作。
    if not path.is_absolute() and not path.exists():
        candidate = config.PROJECT_ROOT / path
        if candidate.exists():
            path = candidate
    try:
        path = path.resolve(strict=True)
    except FileNotFoundError:
        raise SourceError(f"路径不存在：{raw}") from None
    except OSError as exc:
        raise SourceError(f"无法访问这个路径：{raw}（{exc}）") from None

    if not path.is_dir():
        raise SourceError(f"这不是一个文件夹：{path}")

    lowered = str(path).lower().rstrip("\\/")
    if lowered in _FORBIDDEN_LOCAL:
        raise SourceError("为了安全，请不要直接扫描系统目录或整个磁盘根目录。")
    if len(path.parts) == 1:
        raise SourceError("为了安全，请不要扫描整个磁盘（请选择具体的项目文件夹）。")

    if config.ALLOWED_LOCAL_ROOTS:
        allowed = [Path(item).expanduser().resolve() for item in config.ALLOWED_LOCAL_ROOTS]
        if not any(path == root or root in path.parents for root in allowed):
            raise SourceError(
                "这个路径不在允许的范围内。请检查 .env 里的 REPOLENS_ALLOWED_ROOTS 配置。"
            )

    return path


def clone_github(source: str, progress=None) -> tuple[Path, str]:
    """克隆 GitHub 仓库到本地缓存目录，返回 (目录, 说明)。

    为了不重复下载，同一个地址第二次会直接复用本地缓存。
    """
    owner, repo = parse_github(source)
    url = f"https://github.com/{owner}/{repo}.git"

    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", f"{owner}__{repo}")[:60]
    dest = config.REPOS_DIR / f"{safe_name}__{digest}"
    config.REPOS_DIR.mkdir(parents=True, exist_ok=True)

    if (dest / ".git").exists():
        return dest, f"复用本地缓存：{dest.name}"

    if dest.exists() and any(dest.iterdir()):
        # 目录存在但不是完整的 git 仓库（可能是上次克隆失败留下的），清掉重来。
        shutil.rmtree(dest, ignore_errors=True)

    git_exe = shutil.which("git")
    if not git_exe:
        raise SourceError(
            "没有找到 git 命令。请先安装 Git（https://git-scm.com/），"
            "或者改用本地路径分析。"
        )

    if progress:
        progress(f"正在克隆 {owner}/{repo}（只拉取最新一次提交）…")

    started = time.time()
    command = [
        git_exe,
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--no-tags",
        url,
        str(dest),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=config.CLONE_TIMEOUT_SECONDS,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(dest, ignore_errors=True)
        raise SourceError(
            f"克隆超时（>{config.CLONE_TIMEOUT_SECONDS} 秒）。"
            "仓库可能太大，或者网络不稳定，请稍后重试。"
        ) from None

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()[-500:]
        shutil.rmtree(dest, ignore_errors=True)
        raise SourceError(
            "克隆失败。请确认仓库地址正确、仓库是公开的，并且网络可以访问 GitHub。\n"
            f"git 输出：{detail}"
        )

    elapsed = time.time() - started
    return dest, f"克隆完成，用时 {elapsed:.1f} 秒"


def check_repo_size(root: Path, limit_mb: int | None = None) -> tuple[float, bool]:
    """粗略统计仓库体积（MB），返回 (体积, 是否超过限制)。"""
    limit_mb = limit_mb or config.MAX_CLONE_MB
    total = 0
    files = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name.lower() not in {".git"}]
        for filename in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, filename))
            except OSError:
                continue
            files += 1
            if files > 20000:
                break
        if files > 20000:
            break
    size_mb = total / (1024 * 1024)
    return size_mb, size_mb > limit_mb
