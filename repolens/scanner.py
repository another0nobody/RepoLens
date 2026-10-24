"""仓库扫描器：纯 Python 的"体力活"，不调用大模型。

【给初学者：为什么不让大模型直接读仓库？】
一个大模型一次能读的文本是有限的（上下文窗口），而真实仓库可能有几千个文件。
更重要的是：大模型可能会"看漏"或"编造"，而"这个文件里写了 import fastapi"
是可以精确数出来的。

所以本项目采用分工：
    - scanner.py（本文件）：精确地数文件、读依赖清单、提取 import，产出"事实"；
    - Agent（agent.py）：拿着这些事实去理解、归纳、写解释。

这种"工具负责事实，模型负责解释"的思路，是构建可靠 Agent 的关键。

本文件主要做四件事：
    1. 遍历目录，统计语言和代码行数；
    2. 解析依赖清单（requirements.txt / package.json / pom.xml / go.mod ...）；
    3. 从源代码里提取 import，找出"哪个模块用了哪个技术"；
    4. 汇总成 TechHit（技术命中）列表。
"""

from __future__ import annotations

import json
import os
import re
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from . import catalog

Progress = Callable[[str], None] | None

# 扫描上限：防止有人误选一个巨大的目录，把内存/时间耗光。
MAX_FILES = 8000
MAX_CONTENT_FILES = 2600
MAX_FILE_BYTES = 600_000
MAX_MODULES_PER_TECH = 20
MAX_EVIDENCE_PER_TECH = 8

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "bower_components",
    "dist",
    "build",
    "out",
    "target",
    "bin",
    "obj",
    "venv",
    "env",
    "__pycache__",
    "site-packages",
    "coverage",
    ".nyc_output",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".gradle",
    ".m2",
    "vendor",
    "pods",
    "deriveddata",
    ".terraform",
    ".cache",
    ".idea",
    ".vscode",
}
ALLOW_DOT_DIRS = {".github", ".gitlab", ".devcontainer", ".circleci"}

IGNORE_SUFFIXES = {
    ".pyc", ".pyo", ".pyd", ".class", ".jar", ".war", ".ear", ".exe", ".dll",
    ".so", ".dylib", ".a", ".lib", ".o", ".obj", ".png", ".jpg", ".jpeg",
    ".gif", ".bmp", ".ico", ".webp", ".svg", ".pdf", ".zip", ".tar", ".gz",
    ".bz2", ".7z", ".rar", ".mp3", ".mp4", ".mov", ".avi", ".woff", ".woff2",
    ".ttf", ".eot", ".otf", ".psd", ".ai", ".sketch", ".fig", ".db", ".sqlite",
    ".sqlite3", ".parquet", ".arrow", ".pkl", ".pt", ".pth", ".onnx", ".bin",
}
IGNORE_FILENAMES = {
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock",
    "cargo.lock", "pipfile.lock", "composer.lock", "gemfile.lock", "uv.lock",
    "go.sum",
}

TEXT_SUFFIXES = {
    ".py", ".pyi", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue",
    ".svelte", ".java", ".kt", ".kts", ".go", ".rs", ".c", ".h", ".cc",
    ".cpp", ".cxx", ".hpp", ".hh", ".cs", ".php", ".rb", ".swift", ".scala",
    ".dart", ".lua", ".sh", ".bash", ".ps1", ".sql", ".html", ".css",
    ".scss", ".sass", ".less", ".md", ".txt", ".toml", ".yaml", ".yml",
    ".json", ".xml", ".gradle", ".tf", ".proto", ".ini", ".cfg", ".conf",
    ".env", ".properties", ".graphql", ".gql", ".ipynb", ".m", ".mm",
}

# 语言识别表：(展示名, 是否算"代码语言")
LANGUAGE_BY_SUFFIX: dict[str, tuple[str, bool]] = {
    ".py": ("Python", True),
    ".pyi": ("Python", True),
    ".ipynb": ("Jupyter Notebook", True),
    ".js": ("JavaScript", True),
    ".jsx": ("JavaScript", True),
    ".mjs": ("JavaScript", True),
    ".cjs": ("JavaScript", True),
    ".ts": ("TypeScript", True),
    ".tsx": ("TypeScript", True),
    ".vue": ("Vue", True),
    ".svelte": ("Svelte", True),
    ".java": ("Java", True),
    ".kt": ("Kotlin", True),
    ".kts": ("Kotlin", True),
    ".go": ("Go", True),
    ".rs": ("Rust", True),
    ".c": ("C", True),
    ".h": ("C", True),
    ".cc": ("C++", True),
    ".cpp": ("C++", True),
    ".cxx": ("C++", True),
    ".hpp": ("C++", True),
    ".hh": ("C++", True),
    ".cs": ("C#", True),
    ".php": ("PHP", True),
    ".rb": ("Ruby", True),
    ".swift": ("Swift", True),
    ".scala": ("Scala", True),
    ".dart": ("Dart", True),
    ".lua": ("Lua", True),
    ".sh": ("Shell", True),
    ".bash": ("Shell", True),
    ".ps1": ("PowerShell", True),
    ".sql": ("SQL", True),
    ".html": ("HTML", False),
    ".css": ("CSS", False),
    ".scss": ("SCSS", False),
    ".sass": ("SCSS", False),
    ".less": ("Less", False),
    ".md": ("Markdown", False),
    ".json": ("JSON", False),
    ".yaml": ("YAML", False),
    ".yml": ("YAML", False),
    ".toml": ("TOML", False),
    ".xml": ("XML", False),
    ".proto": ("Protocol Buffers", False),
    ".tf": ("HCL", False),
}

# 语言 -> 依赖生态，用于查词典时区分（比如 java 的 import 是点号分隔的）。
LANGUAGE_ECOSYSTEM = {
    "Python": "python",
    "Jupyter Notebook": "python",
    "JavaScript": "js",
    "TypeScript": "js",
    "Vue": "js",
    "Svelte": "js",
    "Java": "java",
    "Kotlin": "java",
    "Rust": "rust",
    "Go": "go",
}

PY_STDLIB = {
    "abc", "argparse", "ast", "asyncio", "base64", "binascii", "bisect", "builtins",
    "calendar", "cmath", "codecs", "collections", "concurrent", "configparser",
    "contextlib", "copy", "csv", "ctypes", "dataclasses", "datetime", "decimal",
    "difflib", "dis", "email", "enum", "errno", "faulthandler", "filecmp",
    "fileinput", "fnmatch", "fractions", "ftplib", "functools", "gc", "getopt",
    "getpass", "gettext", "glob", "gzip", "hashlib", "heapq", "hmac", "html",
    "http", "imaplib", "importlib", "inspect", "io", "ipaddress", "itertools",
    "json", "keyword", "linecache", "locale", "logging", "lzma", "mailbox",
    "math", "mimetypes", "multiprocessing", "numbers", "operator", "os",
    "pathlib", "pickle", "pkgutil", "platform", "plistlib", "poplib", "pprint",
    "profile", "pstats", "queue", "random", "re", "readline", "reprlib",
    "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil",
    "signal", "site", "smtplib", "socket", "socketserver", "sqlite3", "ssl",
    "stat", "statistics", "string", "stringprep", "struct", "subprocess",
    "sys", "sysconfig", "tarfile", "tempfile", "termios", "textwrap", "threading",
    "time", "timeit", "tkinter", "token", "tokenize", "tomllib", "traceback",
    "tracemalloc", "types", "typing", "unicodedata", "unittest", "urllib",
    "uuid", "venv", "warnings", "wave", "weakref", "webbrowser", "xml",
    "zipapp", "zipfile", "zlib", "zoneinfo", "__future__",
}

JS_BUILTINS = {
    "assert", "buffer", "child_process", "cluster", "console", "constants",
    "crypto", "dgram", "diagnostics_channel", "dns", "domain", "events", "fs",
    "http", "http2", "https", "inspector", "module", "net", "os", "path",
    "perf_hooks", "process", "punycode", "querystring", "readline", "repl",
    "stream", "string_decoder", "timers", "tls", "trace_events", "tty", "url",
    "util", "v8", "vm", "wasm", "worker_threads", "zlib", "node",
}

JAVA_STDLIB_PREFIXES = ("java.", "javax.", "sun.", "com.sun.", "kotlin.", "scala.")
GO_STDLIB_HINT = re.compile(r"^[a-z0-9]+(/[a-z0-9]+)*$")
C_STD_HEADERS = {
    "stdio.h", "stdlib.h", "string.h", "math.h", "stdint.h", "stdbool.h",
    "stddef.h", "time.h", "assert.h", "ctype.h", "errno.h", "float.h",
    "limits.h", "locale.h", "setjmp.h", "signal.h", "stdarg.h", "wchar.h",
    "wctype.h", "unistd.h", "sys/types.h", "sys/stat.h", "fcntl.h", "dirent.h",
    "pthread.h", "iostream", "vector", "string", "map", "set", "algorithm",
    "memory", "utility", "cmath", "cstdio", "cstdlib", "cstring", "cstdint",
    "array", "queue", "stack", "tuple", "optional", "variant", "chrono",
    "thread", "mutex", "atomic", "functional", "numeric", "limits", "bits/stdc++.h",
}


# ============================================================================
# 数据结构
# ============================================================================
@dataclass
class ImportRef:
    """一条 import 语句。"""

    module: str
    line: int
    text: str


@dataclass
class DepRef:
    """依赖清单里的一条依赖（或一个由配置推导出的技术）。"""

    name: str
    version: str
    ecosystem: str
    path: str
    line: int
    text: str


@dataclass
class Manifest:
    """一个依赖清单/配置文件。"""

    path: str
    kind: str
    deps: list[DepRef] = field(default_factory=list)
    note: str = ""


@dataclass
class TechHit:
    """扫描器对"一项技术"的完整记录。"""

    key: str
    name: str
    category: str
    hint: str
    version: str = ""
    confidence: str = "中"
    sources: set[str] = field(default_factory=set)
    evidence: list[dict] = field(default_factory=list)
    modules: dict[str, dict] = field(default_factory=dict)
    version_score: int = -1  # 内部使用：版本号的"可信优先级"，越大越优先

    def add_evidence(self, path: str, line: int, text: str, kind: str) -> None:
        if len(self.evidence) >= MAX_EVIDENCE_PER_TECH:
            return
        for item in self.evidence:
            if item["path"] == path and item["line"] == line:
                return
        self.evidence.append(
            {
                "path": path,
                "line": line,
                "text": (text or "").strip()[:180],
                "kind": kind,
            }
        )

    def add_module(self, path: str, line: int, snippet: str, kind: str = "导入") -> None:
        if path in self.modules:
            return
        if len(self.modules) >= MAX_MODULES_PER_TECH:
            return
        self.modules[path] = {
            "path": path,
            "line": line,
            "snippet": (snippet or "").strip()[:200],
            "kind": kind,
            "role": guess_module_role(path),
        }

    def to_dict(self) -> dict:
        modules = sorted(self.modules.values(), key=lambda item: item["path"])
        return {
            "key": self.key,
            "name": self.name,
            "category": self.category,
            "hint": self.hint,
            "version": self.version,
            "confidence": self.confidence,
            "sources": sorted(self.sources),
            "evidence": self.evidence,
            "modules": modules,
            "module_count": len(modules),
        }


@dataclass
class Snapshot:
    """一次扫描的全部结果。"""

    root: Path
    repo_name: str
    source: str
    source_type: str
    files: list[str]
    file_count: int
    code_file_count: int
    total_loc: int
    size_bytes: int
    truncated: bool
    languages: list[dict]
    manifests: list[Manifest]
    techs: list[TechHit]
    top_dirs: list[dict]
    entry_points: list[str]
    readme: str
    scan_seconds: float
    omitted_dependencies: int = 0

    def to_dict(self) -> dict:
        return {
            "repo_name": self.repo_name,
            "source": self.source,
            "source_type": self.source_type,
            "root": str(self.root),
            "stats": {
                "file_count": self.file_count,
                "code_file_count": self.code_file_count,
                "total_loc": self.total_loc,
                "size_mb": round(self.size_bytes / (1024 * 1024), 2),
                "truncated": self.truncated,
                "scan_seconds": round(self.scan_seconds, 2),
                "omitted_dependencies": self.omitted_dependencies,
            },
            "languages": self.languages,
            "manifests": [
                {"path": item.path, "kind": item.kind, "dependency_count": len(item.deps), "note": item.note}
                for item in self.manifests
            ],
            "techs": [tech.to_dict() for tech in self.techs],
            "top_dirs": self.top_dirs,
            "entry_points": self.entry_points,
            "readme": self.readme,
        }


class SnapshotError(Exception):
    """扫描失败时抛出。"""


# ============================================================================
# 小工具函数
# ============================================================================
def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _should_skip_dir(name: str) -> bool:
    lowered = name.lower()
    if lowered in IGNORE_DIRS:
        return True
    if lowered.startswith(".") and lowered not in ALLOW_DOT_DIRS:
        return True
    return False


def _read_text_file(path: Path) -> str:
    """尽量把文件读成文本；二进制文件返回空字符串。"""
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return ""
        data = path.read_bytes()
    except OSError:
        return ""

    # Windows 上有些文件是 UTF-16 编码（记事本另存为"Unicode"），先按 BOM 识别，
    # 否则会被下面的"\x00 表示二进制"判断误伤。
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            pass

    if b"\x00" in data[:2048]:
        return ""
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return ""


def _count_loc(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def _clean_snippet(line: str) -> str:
    return line.strip()[:200]


def guess_module_role(path: str) -> str:
    """根据文件路径猜它的"角色"，用于网页展示（模型没给角色时的兜底）。"""
    lowered = path.lower()
    filename = lowered.rsplit("/", 1)[-1]
    if any(part in lowered for part in ("/test", "test/", "tests/", "_test.", ".test.", ".spec.", "spec/")):
        return "测试"
    if any(part in lowered for part in ("/config", "config/", "settings", ".env", "conf/")):
        return "配置"
    if any(part in lowered for part in ("/api", "api/", "/routes", "routes/", "/controller", "controller", "/views", "views/")):
        return "接口层"
    if any(part in lowered for part in ("/models", "model/", "/entity", "entities/", "/schema", "schemas/")):
        return "数据模型"
    if any(part in lowered for part in ("/services", "service/", "/usecase", "/business")):
        return "业务逻辑"
    if any(part in lowered for part in ("/db", "database", "/repository", "/dao", "/migrations")):
        return "数据访问"
    if any(part in lowered for part in ("/middleware", "/middlewares", "/plugins", "/utils", "/common", "/shared")):
        return "公共能力"
    if any(part in lowered for part in ("/components", "component/", "/pages", "pages/", "/views", "/ui")):
        return "界面组件"
    if any(part in lowered for part in ("/scripts", "script/", "/tools", "/cli")):
        return "脚本/工具"
    if filename in {"main.py", "app.py", "main.go", "main.rs", "main.ts", "index.js", "index.ts", "manage.py", "server.py"}:
        return "入口"
    if any(part in lowered for part in ("dockerfile", "docker-compose", "compose.", ".github/", "k8s", "helm", "deploy")):
        return "部署"
    return "源码"


# ============================================================================
# 依赖清单解析
# ============================================================================
def _dep_from_spec(spec: str, path: str, line: int, ecosystem: str) -> DepRef | None:
    """把 "fastapi[all]>=0.115,<1.0" 这样的字符串拆成名字 + 版本。"""
    text = spec.strip().strip(",").strip("\"'")
    if not text or text.startswith(("#", "-", "git+", "http://", "https://")):
        return None
    # 去掉环境标记（; python_version > "3.8"）
    text = text.split(";", 1)[0].strip()
    # extras：[all]
    text = re.sub(r"\[[^\]]*\]", "", text)
    match = re.match(r"^([A-Za-z0-9@][A-Za-z0-9@._/\-]*)\s*(.*)$", text)
    if not match:
        return None
    name = match.group(1)
    rest = match.group(2)
    version = ""
    version_match = re.search(r"(?:===|==|~=|>=|<=|>|<)\s*([0-9][0-9A-Za-z.\-+_]*)", rest)
    if version_match:
        version = version_match.group(1)
    if len(name) < 2:
        return None
    return DepRef(name=name, version=version, ecosystem=ecosystem, path=path, line=line, text=_clean_snippet(spec))


def _parse_requirements(text: str, path: str) -> list[DepRef]:
    deps: list[DepRef] = []
    buffer = ""
    buffer_line = 0
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # 处理 \ 续行
        if line.endswith("\\"):
            if not buffer:
                buffer_line = number
            buffer += line[:-1].strip() + " "
            continue
        merged = (buffer + line).strip()
        buffer = ""
        if not merged or merged.startswith(("-", "git+", "http://", "https://")):
            continue
        dep = _dep_from_spec(merged, path, buffer_line or number, "python")
        if dep:
            deps.append(dep)
    if buffer.strip():
        dep = _dep_from_spec(buffer, path, buffer_line, "python")
        if dep:
            deps.append(dep)
    return deps


def _parse_pyproject(text: str, path: str) -> list[DepRef]:
    try:
        data = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, ValueError):
        return []
    deps: list[DepRef] = []

    project = data.get("project") or {}
    for spec in project.get("dependencies") or []:
        if isinstance(spec, str):
            dep = _dep_from_spec(spec, path, 1, "python")
            if dep:
                deps.append(dep)
    optional = project.get("optional-dependencies") or {}
    if isinstance(optional, dict):
        for group_specs in optional.values():
            for spec in group_specs or []:
                if isinstance(spec, str):
                    dep = _dep_from_spec(spec, path, 1, "python")
                    if dep:
                        deps.append(dep)

    poetry = (data.get("tool") or {}).get("poetry") or {}
    for table_name in ("dependencies", "dev-dependencies"):
        table = poetry.get(table_name) or {}
        for name, value in table.items():
            if name.lower() == "python":
                continue
            version = ""
            if isinstance(value, str):
                version = value.lstrip("^~>=< ")
            elif isinstance(value, dict):
                version = str(value.get("version", "")).lstrip("^~>=< ")
            deps.append(
                DepRef(
                    name=name,
                    version=version,
                    ecosystem="python",
                    path=path,
                    line=1,
                    text=f"{name} = {value}",
                )
            )
    return deps


def _parse_setup_py(text: str, path: str) -> list[DepRef]:
    match = re.search(r"install_requires\s*=\s*\[(.*?)\]", text, re.S)
    if not match:
        return []
    deps = []
    for spec in re.findall(r"[\"']([^\"']+)[\"']", match.group(1)):
        dep = _dep_from_spec(spec, path, 1, "python")
        if dep:
            deps.append(dep)
    return deps


def _parse_setup_cfg(text: str, path: str) -> list[DepRef]:
    deps = []
    in_block = False
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if line.startswith("install_requires"):
            in_block = "=" in line and not line.endswith("=")
            continue
        if in_block:
            if line and not raw.startswith((" ", "\t")):
                in_block = False
                continue
            if not line or line.startswith("#"):
                continue
            dep = _dep_from_spec(line, path, number, "python")
            if dep:
                deps.append(dep)
    return deps


def _parse_pipfile(text: str, path: str) -> list[DepRef]:
    try:
        data = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, ValueError):
        return []
    deps = []
    for table_name in ("packages", "dev-packages"):
        for name, value in (data.get(table_name) or {}).items():
            version = value if isinstance(value, str) else str(value.get("version", ""))
            deps.append(
                DepRef(name=name, version=version.strip("*= "), ecosystem="python", path=path, line=1, text=f"{name} = {value}")
            )
    return deps


def _parse_package_json(text: str, path: str) -> list[DepRef]:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    deps = []
    for table_name in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        table = data.get(table_name) or {}
        if not isinstance(table, dict):
            continue
        for name, version in table.items():
            if catalog.should_skip_dependency(name):
                continue
            deps.append(
                DepRef(
                    name=name,
                    version=str(version).lstrip("^~>=< "),
                    ecosystem="js",
                    path=path,
                    line=1,
                    text=f'"{name}": "{version}"',
                )
            )
    return deps


def _parse_pom_xml(text: str, path: str) -> list[DepRef]:
    try:
        import xml.etree.ElementTree as ET

        root = ET.fromstring(text)
    except Exception:
        return []

    deps = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag != "dependency":
            continue
        values = {}
        for child in element:
            child_tag = child.tag.rsplit("}", 1)[-1]
            values[child_tag] = (child.text or "").strip()
        artifact = values.get("artifactId", "")
        if not artifact:
            continue
        version = values.get("version", "")
        deps.append(
            DepRef(
                name=artifact,
                version=version,
                ecosystem="java",
                path=path,
                line=1,
                text=f"{values.get('groupId', '')}:{artifact}:{version}".strip(":"),
            )
        )
    return deps


def _parse_gradle(text: str, path: str) -> list[DepRef]:
    deps = []
    pattern = re.compile(
        r"(?:implementation|api|compile|compileOnly|runtimeOnly|testImplementation|testRuntimeOnly|annotationProcessor|kapt)\s*\(?\s*[\"']([^\"']+)[\"']"
    )
    for number, raw in enumerate(text.splitlines(), start=1):
        for coordinate in pattern.findall(raw):
            parts = coordinate.split(":")
            if len(parts) < 2:
                continue
            artifact = parts[1]
            version = parts[2] if len(parts) > 2 else ""
            deps.append(DepRef(name=artifact, version=version, ecosystem="java", path=path, line=number, text=_clean_snippet(raw)))
    return deps


def _parse_go_mod(text: str, path: str) -> list[DepRef]:
    deps = []
    in_block = False
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if line.startswith("require ("):
            in_block = True
            continue
        if in_block and line == ")":
            in_block = False
            continue
        candidate = ""
        if in_block:
            candidate = line
        elif line.startswith("require "):
            candidate = line[len("require "):].strip()
        if not candidate or candidate.startswith("//"):
            continue
        parts = candidate.split()
        if len(parts) < 2:
            continue
        module = parts[0]
        version = parts[1].lstrip("v")  # Go 的版本号习惯写成 v1.2.3，展示时去掉前缀
        deps.append(DepRef(name=module, version=version, ecosystem="go", path=path, line=number, text=_clean_snippet(raw)))
    return deps


def _parse_cargo(text: str, path: str) -> list[DepRef]:
    try:
        data = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, ValueError):
        return []
    deps = []
    tables = [data.get("dependencies") or {}, data.get("dev-dependencies") or {}]
    workspace = data.get("workspace") or {}
    tables.append(workspace.get("dependencies") or {})
    for table in tables:
        if not isinstance(table, dict):
            continue
        for name, value in table.items():
            version = ""
            if isinstance(value, str):
                version = value.lstrip("^~>=< ")
            elif isinstance(value, dict):
                version = str(value.get("version", ""))
            deps.append(DepRef(name=name, version=version, ecosystem="rust", path=path, line=1, text=f"{name} = {value}"))
    return deps


def _parse_composer(text: str, path: str) -> list[DepRef]:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    deps = []
    for table_name in ("require", "require-dev"):
        for name, version in (data.get(table_name) or {}).items():
            if "/" not in name:
                continue
            deps.append(DepRef(name=name, version=str(version), ecosystem="php", path=path, line=1, text=f"{name}: {version}"))
    return deps


def _parse_gemfile(text: str, path: str) -> list[DepRef]:
    deps = []
    for number, raw in enumerate(text.splitlines(), start=1):
        match = re.search(r"^\s*gem\s+[\"']([^\"']+)[\"'](?:\s*,\s*[\"']([^\"']+)[\"'])?", raw)
        if match:
            deps.append(DepRef(name=match.group(1), version=match.group(2) or "", ecosystem="ruby", path=path, line=number, text=_clean_snippet(raw)))
    return deps


def _parse_csproj(text: str, path: str) -> list[DepRef]:
    deps = []
    for match in re.finditer(r"<PackageReference\s+Include=\"([^\"]+)\"\s+Version=\"([^\"]+)\"", text):
        deps.append(DepRef(name=match.group(1), version=match.group(2), ecosystem="dotnet", path=path, line=1, text=match.group(0)))
    return deps


def _docker_image_base(image: str) -> str:
    """把 bitnami/redis:7-alpine 变成 redis。"""
    image = image.strip().split("@", 1)[0]
    image = image.split("/")[-1]
    image = image.split(":", 1)[0]
    mapping = {
        "eclipse-temurin": "java",
        "temurin": "java",
        "openjdk": "java",
        "golang": "go",
        "node": "node",
        "mssql": "sqlserver",
        "postgres": "postgres",
        "mongo": "mongodb",
        "mongo-express": "",
        "redis": "redis",
        "rabbitmq": "rabbitmq",
        "kafka": "kafka",
        "zookeeper": "",
        "elasticsearch": "elasticsearch",
        "opensearch": "",
        "minio": "minio",
        "milvus": "milvus",
        "qdrant": "qdrant",
        "chroma": "chroma",
        "nginx": "nginx",
        "traefik": "",
        "grafana": "grafana",
        "prometheus": "prometheus",
        "jaeger": "jaeger",
        "jenkins": "jenkins",
    }
    return mapping.get(image, image)


def _known_base_image(image: str) -> bool:
    """这个基础镜像/服务镜像是不是我们认识的技术？

    自定义镜像（例如 mycompany/order-api）没有通用意义，跳过可以避免
    「其他依赖」里出现一堆镜像名。认识的运行时/数据库镜像才保留。
    """
    base = _docker_image_base(image)
    if not base:
        return False
    return catalog.lookup(base) is not None


def _parse_dockerfile(text: str, path: str) -> tuple[list[DepRef], list[str]]:
    deps = [DepRef(name="Docker", version="", ecosystem="docker", path=path, line=1, text="Dockerfile")]
    images = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line.upper().startswith("FROM "):
            continue
        image = line.split()[1]
        if image.lower() == "scratch":
            continue
        images.append(image)
        if not _known_base_image(image):
            continue
        base = _docker_image_base(image)
        if base:
            deps.append(
                DepRef(name=base, version="", ecosystem="docker", path=path, line=number, text=_clean_snippet(raw))
            )
    return deps, images


def _parse_compose(text: str, path: str) -> list[DepRef]:
    deps = [DepRef(name="Docker Compose", version="", ecosystem="docker", path=path, line=1, text="docker compose")]
    images: list[str] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("image:"):
            image = stripped.split(":", 1)[1].strip().strip("\"'")
            if image:
                images.append(image)
                if _known_base_image(image):
                    base = _docker_image_base(image)
                    if base:
                        deps.append(DepRef(name=base, version="", ecosystem="docker", path=path, line=number, text=_clean_snippet(raw)))
        # 只根据 image 识别服务技术；服务名（如 db/cache）太随意，容易误判，不采用。
    return deps


MANIFEST_NAMES = {
    "requirements.txt": "requirements",
    "pyproject.toml": "pyproject",
    "setup.py": "setup.py",
    "setup.cfg": "setup.cfg",
    "pipfile": "pipfile",
    "package.json": "package.json",
    "pom.xml": "pom.xml",
    "go.mod": "go.mod",
    "cargo.toml": "cargo",
    "composer.json": "composer",
    "gemfile": "gemfile",
    "dockerfile": "dockerfile",
    "makefile": "makefile",
    "nginx.conf": "nginx",
    "alembic.ini": "alembic",
    "procfile": "procfile",
}


def parse_manifest(relative: str, text: str) -> Manifest | None:
    """识别并解析一个文件。不是清单文件就返回 None。"""
    name = relative.rsplit("/", 1)[-1]
    lowered = name.lower()
    kind = MANIFEST_NAMES.get(lowered)

    if not kind:
        if lowered.startswith("requirements") and lowered.endswith(".txt"):
            kind = "requirements"
        elif lowered.startswith("docker-compose") or (lowered.startswith("compose") and lowered.endswith((".yml", ".yaml"))):
            kind = "compose"
        elif lowered.endswith(".csproj"):
            kind = "csproj"
        elif lowered in {"build.gradle", "build.gradle.kts"}:
            kind = "gradle"
        elif lowered.startswith("dockerfile"):
            kind = "dockerfile"
        elif lowered.startswith(".env") and lowered.endswith((".example", ".sample", ".template")):
            kind = "env"
        elif lowered in {".gitlab-ci.yml", ".gitlab-ci.yaml"}:
            kind = "gitlab-ci"
        elif relative.startswith(".github/workflows/") and lowered.endswith((".yml", ".yaml")):
            kind = "github-actions"
        elif lowered.endswith(".tf"):
            kind = "terraform"
        elif lowered.endswith((".yml", ".yaml")) and ("apiVersion:" in text and "kind:" in text):
            kind = "kubernetes"

    if not kind:
        return None

    manifest = Manifest(path=relative, kind=kind)
    try:
        if kind == "requirements":
            manifest.deps = _parse_requirements(text, relative)
        elif kind == "pyproject":
            manifest.deps = _parse_pyproject(text, relative)
        elif kind == "setup.py":
            manifest.deps = _parse_setup_py(text, relative)
        elif kind == "setup.cfg":
            manifest.deps = _parse_setup_cfg(text, relative)
        elif kind == "pipfile":
            manifest.deps = _parse_pipfile(text, relative)
        elif kind == "package.json":
            manifest.deps = _parse_package_json(text, relative)
        elif kind == "pom.xml":
            manifest.deps = _parse_pom_xml(text, relative)
        elif kind == "gradle":
            manifest.deps = _parse_gradle(text, relative)
        elif kind == "go.mod":
            manifest.deps = _parse_go_mod(text, relative)
        elif kind == "cargo":
            manifest.deps = _parse_cargo(text, relative)
        elif kind == "composer":
            manifest.deps = _parse_composer(text, relative)
        elif kind == "gemfile":
            manifest.deps = _parse_gemfile(text, relative)
        elif kind == "csproj":
            manifest.deps = _parse_csproj(text, relative)
        elif kind == "dockerfile":
            manifest.deps, images = _parse_dockerfile(text, relative)
            manifest.note = "基础镜像：" + "、".join(images[:5]) if images else ""
        elif kind == "compose":
            manifest.deps = _parse_compose(text, relative)
        elif kind == "github-actions":
            manifest.deps = [DepRef(name="GitHub Actions", version="", ecosystem="ci", path=relative, line=1, text="GitHub Actions workflow")]
        elif kind == "gitlab-ci":
            manifest.deps = [DepRef(name="GitLab CI", version="", ecosystem="ci", path=relative, line=1, text="GitLab CI pipeline")]
        elif kind == "kubernetes":
            manifest.deps = [DepRef(name="Kubernetes", version="", ecosystem="k8s", path=relative, line=1, text="Kubernetes manifest")]
        elif kind == "terraform":
            manifest.deps = [DepRef(name="Terraform", version="", ecosystem="iac", path=relative, line=1, text="Terraform")]
        elif kind == "nginx":
            manifest.deps = [DepRef(name="Nginx", version="", ecosystem="server", path=relative, line=1, text="nginx.conf")]
        elif kind == "makefile":
            manifest.deps = [DepRef(name="Make", version="", ecosystem="build", path=relative, line=1, text="Makefile")]
        elif kind == "alembic":
            manifest.deps = [DepRef(name="Alembic", version="", ecosystem="python", path=relative, line=1, text="alembic.ini")]
    except Exception:
        # 单个清单解析失败不应该让整个扫描失败，忽略它继续扫其他文件。
        manifest.note = "该文件解析失败，已跳过"
    return manifest


# ============================================================================
# import 提取
# ============================================================================
_PY_IMPORT = re.compile(r"^[ \t]*(?:from\s+([A-Za-z_][\w.]*)\s+import|import\s+([A-Za-z_][\w.]*))", re.M)
_JS_IMPORT = re.compile(
    r"(?:\bfrom\s*|\brequire\s*\(\s*|\bimport\s*\(\s*)[\"']([^\"']+)[\"']|^\s*import\s+[\"']([^\"']+)[\"']",
    re.M,
)
_JAVA_IMPORT = re.compile(r"^[ \t]*(?:import|using)\s+(?:static\s+)?([\w.]+)\s*;?", re.M)
_GO_QUOTED = re.compile(r"\"([A-Za-z0-9_./\-]+)\"")
_RUST_IMPORT = re.compile(r"^[ \t]*(?:use|extern\s+crate)\s+([A-Za-z0-9_]+)", re.M)
_RUBY_REQUIRE = re.compile(r"^[ \t]*require\s+[\"']([^\"']+)[\"']", re.M)
_PHP_USE = re.compile(r"^[ \t]*use\s+([\w\\]+)\s*;", re.M)
_C_INCLUDE = re.compile(r"^[ \t]*#\s*include\s*[<\"]([^>\"]+)[>\"]", re.M)


def extract_imports(text: str, language: str) -> list[ImportRef]:
    """按语言提取 import 语句，返回 (模块名, 行号, 原文)。"""
    refs: list[ImportRef] = []
    lines = text.splitlines()
    newline_positions = [index for index, char in enumerate(text) if char == "\n"]

    def add(module: str, position: int) -> None:
        module = module.strip()
        if not module:
            return
        # 用二分查找把"字符位置"换算成"行号"，比每次从 0 数一遍快很多。
        import bisect

        line_number = bisect.bisect_left(newline_positions, position) + 1
        snippet = lines[line_number - 1] if line_number - 1 < len(lines) else module
        refs.append(ImportRef(module=module, line=line_number, text=_clean_snippet(snippet)))

    if language in {"Python", "Jupyter Notebook"}:
        for match in _PY_IMPORT.finditer(text):
            module = match.group(1) or match.group(2) or ""
            root = module.split(".", 1)[0]
            if not root or root in PY_STDLIB or module.startswith("."):
                continue
            add(module, match.start(1) if match.group(1) else match.start(2))
    elif language in {"JavaScript", "TypeScript", "Vue", "Svelte"}:
        for match in _JS_IMPORT.finditer(text):
            module = match.group(1) or match.group(2) or ""
            if not module or module.startswith((".", "/", "~", "#", "@/", "node:")):
                continue
            if module.startswith("@/"):
                continue
            root = "/".join(module.split("/")[:2]) if module.startswith("@") else module.split("/", 1)[0]
            if root in JS_BUILTINS:
                continue
            add(root, match.start(1) if match.group(1) else match.start(2))
    elif language in {"Java", "Kotlin"}:
        for match in _JAVA_IMPORT.finditer(text):
            module = match.group(1).rstrip(".")
            if module.startswith(JAVA_STDLIB_PREFIXES):
                continue
            add(module, match.start(1))
    elif language == "Go":
        in_block = False
        for number, raw in enumerate(lines, start=1):
            stripped = raw.strip()
            if stripped.startswith("import ("):
                in_block = True
                continue
            if in_block and stripped == ")":
                in_block = False
                continue
            if in_block or stripped.startswith("import "):
                for module in _GO_QUOTED.findall(stripped):
                    if GO_STDLIB_HINT.match(module):
                        continue
                    refs.append(ImportRef(module=module, line=number, text=_clean_snippet(raw)))
    elif language == "Rust":
        for match in _RUST_IMPORT.finditer(text):
            add(match.group(1), match.start(1))
    elif language == "Ruby":
        for match in _RUBY_REQUIRE.finditer(text):
            add(match.group(1), match.start(1))
    elif language == "PHP":
        for match in _PHP_USE.finditer(text):
            add(match.group(1), match.start(1))
    elif language in {"C", "C++", "C#"}:
        if language == "C#":
            for match in _JAVA_IMPORT.finditer(text):
                module = match.group(1)
                if module.startswith(("System.", "Microsoft.")) and "aspnetcore" not in module.lower():
                    continue
                add(module, match.start(1))
        else:
            for match in _C_INCLUDE.finditer(text):
                module = match.group(1)
                if module in C_STD_HEADERS:
                    continue
                add(module, match.start(1))

    return refs


def _match_import(module: str) -> catalog.TechSpec | None:
    """把 import 名映射到词典里的技术。"""
    spec = catalog.lookup(module)
    if spec is not None:
        return spec
    # Java 的 import 可能比词典条目更长（例如 org.springframework.web.bind），
    # 从最细的层级往上退，逐级尝试。
    if "." in module:
        parts = module.split(".")
        for index in range(len(parts) - 1, 1, -1):
            candidate = ".".join(parts[:index])
            spec = catalog.lookup(candidate)
            if spec is not None:
                return spec
    # Go 的包路径同理，往上退一级。
    if "/" in module:
        parts = module.split("/")
        for index in range(len(parts) - 1, 1, -1):
            candidate = "/".join(parts[:index])
            spec = catalog.lookup(candidate)
            if spec is not None:
                return spec
    return None


# ============================================================================
# 主流程
# ============================================================================
def scan_repository(
    root: Path,
    source: str,
    source_type: str,
    progress: Progress = None,
) -> Snapshot:
    """扫描一个本地目录，返回 Snapshot。"""
    started = time.time()
    root = root.resolve()
    if not root.is_dir():
        raise SnapshotError(f"目录不存在或不可读：{root}")

    if progress:
        progress("开始遍历目录，统计文件与语言…")

    files: list[str] = []
    language_stats: dict[str, dict] = {}
    manifests: list[Manifest] = []
    imports: dict[str, list[ImportRef]] = {}
    total_size = 0
    total_loc = 0
    code_file_count = 0
    truncated = False
    content_files = 0
    readme_text = ""

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = sorted(name for name in dirnames if not _should_skip_dir(name))
        for filename in sorted(filenames):
            if len(files) >= MAX_FILES:
                truncated = True
                break

            full_path = Path(dirpath) / filename
            relative = _relative(full_path, root)
            files.append(relative)

            try:
                size = full_path.stat().st_size
            except OSError:
                size = 0
            total_size += size

            lowered = filename.lower()
            suffix = full_path.suffix.lower()
            if lowered in IGNORE_FILENAMES or suffix in IGNORE_SUFFIXES:
                continue

            language_info = LANGUAGE_BY_SUFFIX.get(suffix)
            language = language_info[0] if language_info else ""
            is_code = language_info[1] if language_info else False
            if language:
                bucket = language_stats.setdefault(language, {"name": language, "files": 0, "loc": 0, "is_code": is_code})
                bucket["files"] += 1

            needs_content = (
                suffix in TEXT_SUFFIXES
                or lowered in MANIFEST_NAMES
                or lowered.startswith(("requirements", "docker-compose", "compose", "dockerfile"))
            )
            if not needs_content or content_files >= MAX_CONTENT_FILES:
                continue

            content_files += 1
            text = _read_text_file(full_path)
            if not text:
                continue

            if is_code and language != "Jupyter Notebook":
                file_loc = _count_loc(text)
                total_loc += file_loc
                code_file_count += 1
                if language in language_stats:
                    language_stats[language]["loc"] += file_loc

            # 读取 README（只取根目录或一级目录下的第一个）
            if not readme_text and lowered.startswith("readme") and suffix in {".md", ".rst", ".txt"}:
                if relative.count("/") <= 1:
                    readme_text = text[:6000]

            manifest = parse_manifest(relative, text)
            if manifest is not None:
                manifests.append(manifest)

            if is_code:
                if language == "Jupyter Notebook":
                    notebook_text, notebook_loc = _notebook_code(text)
                    total_loc += notebook_loc
                    code_file_count += 1
                    if language in language_stats:
                        language_stats[language]["loc"] += notebook_loc
                    refs = extract_imports(notebook_text, "Python")
                else:
                    refs = extract_imports(text, language)
                if refs:
                    imports[relative] = refs

            if len(files) % 400 == 0 and progress:
                progress(f"已扫描 {len(files)} 个文件…")

        if len(files) >= MAX_FILES:
            truncated = True
            break

    if content_files >= MAX_CONTENT_FILES:
        # 文件列表可能是完整的，但内容扫描到达上限，报告里也要如实标注。
        truncated = True

    if progress:
        progress(f"目录遍历完成，共 {len(files)} 个文件；开始识别依赖与 import…")

    languages = _build_language_stats(language_stats, total_loc)
    top_dirs = _build_top_dirs(files)
    entry_points = _find_entry_points(files)
    techs, omitted_dependencies = _build_techs(languages, manifests, imports, progress)

    snapshot = Snapshot(
        root=root,
        repo_name=root.name,
        source=source,
        source_type=source_type,
        files=files,
        file_count=len(files),
        code_file_count=code_file_count,
        total_loc=total_loc,
        size_bytes=total_size,
        truncated=truncated,
        languages=languages,
        manifests=manifests,
        techs=techs,
        top_dirs=top_dirs,
        entry_points=entry_points,
        readme=readme_text,
        scan_seconds=time.time() - started,
        omitted_dependencies=omitted_dependencies,
    )
    if progress:
        progress(f"扫描完成：识别到 {len(languages)} 种语言、{len(techs)} 项技术")
    return snapshot


def _notebook_code(text: str) -> tuple[str, int]:
    """从 .ipynb 里抽出代码单元格，拼成一段类似 Python 的文本。"""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return "", 0
    chunks = []
    loc = 0
    for cell in data.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        code = "".join(source) if isinstance(source, list) else str(source)
        loc += sum(1 for line in code.splitlines() if line.strip())
        chunks.append(code)
    return "\n".join(chunks), loc


def _build_language_stats(language_stats: dict[str, dict], total_loc: int) -> list[dict]:
    total = sum(item["loc"] for item in language_stats.values() if item["is_code"]) or 1
    languages = []
    for item in language_stats.values():
        if item["is_code"]:
            percent = round(item["loc"] / total * 100, 1)
        else:
            percent = None
        languages.append(
            {
                "name": item["name"],
                "files": item["files"],
                "loc": item["loc"],
                "percent": percent,
                "is_code": item["is_code"],
            }
        )
    languages.sort(key=lambda item: (item["loc"], item["files"]), reverse=True)
    return languages


def _build_top_dirs(files: list[str]) -> list[dict]:
    buckets: dict[str, dict] = {}
    for path in files:
        if "/" not in path:
            continue
        top = path.split("/", 1)[0]
        bucket = buckets.setdefault(top, {"name": top, "files": 0})
        bucket["files"] += 1
    result = sorted(buckets.values(), key=lambda item: item["files"], reverse=True)
    return result[:12]


def _find_entry_points(files: list[str]) -> list[str]:
    wanted = {
        "main.py", "app.py", "manage.py", "server.py", "run.py", "wsgi.py",
        "asgi.py", "index.js", "index.ts", "main.js", "main.ts", "main.go",
        "main.rs", "program.cs", "app.tsx", "app.vue", "dockerfile",
        "docker-compose.yml", "docker-compose.yaml", "makefile", "pom.xml",
        "package.json", "pyproject.toml", "requirements.txt", "go.mod",
        "cargo.toml", "index.html",
    }
    result = []
    for path in files:
        lowered = path.lower()
        name = lowered.rsplit("/", 1)[-1]
        if name in wanted:
            result.append(path)
    # 去重并保持稳定顺序；最多 12 个
    seen = set()
    unique = []
    for path in result:
        if path in seen:
            continue
        seen.add(path)
        unique.append(path)
    return unique[:12]


def _build_techs(
    languages: list[dict],
    manifests: list[Manifest],
    imports: dict[str, list[ImportRef]],
    progress: Progress,
) -> tuple[list[TechHit], int]:
    """把语言、依赖、import 汇总成技术命中列表。

    返回 (技术列表, 被省略的陌生依赖数量)。陌生依赖最多展示 24 个，
    其余的只计数，避免"其他依赖"把页面淹没。
    """
    techs: dict[str, TechHit] = {}

    def get_hit(spec: catalog.TechSpec | None, name: str | None = None) -> TechHit:
        if spec is not None:
            key = spec.name.lower()
            display = spec.name
            category = spec.category
            hint = spec.hint
        else:
            display = name or "unknown"
            key = catalog.normalize_name(display)
            category = catalog.guess_generic_category(display)
            hint = "第三方依赖（词典中暂无收录）"
        hit = techs.get(key)
        if hit is None:
            hit = TechHit(key=key, name=display, category=category, hint=hint)
            techs[key] = hit
        return hit

    # 1) 语言：只要这个仓库有该语言的文件，就把它算进技术栈
    for language in languages:
        if not language["is_code"]:
            continue
        if language["name"] in {"Jupyter Notebook", "Vue", "Svelte"}:
            # 这些更像"文件格式/框架"，交给依赖清单去识别，避免分类重复。
            continue
        spec = catalog.lookup(language["name"])
        hit = get_hit(spec, language["name"])
        hit.sources.add("language")
        hit.confidence = "高"
        hit.add_evidence(
            "<语言统计>",
            0,
            f"{language['files']} 个文件，约 {language['loc']} 行代码",
            "语言统计",
        )

    # 2) 依赖清单
    generic_count = 0
    omitted_names: set[str] = set()
    for manifest in manifests:
        for dep in manifest.deps:
            spec = catalog.lookup(dep.name)
            if spec is None and catalog.should_skip_dependency(dep.name):
                continue
            if spec is None:
                # 不认识的依赖：只保留前 24 个，避免"其他依赖"爆炸
                if generic_count >= 24:
                    omitted_names.add(dep.name.lower())
                    continue
                if dep.name.lower() in {name.lower() for name in techs}:
                    continue
                generic_count += 1
                hit = get_hit(None, dep.name)
                hit.confidence = "高"
            else:
                hit = get_hit(spec)
                hit.confidence = "高"
            hit.sources.add("manifest" if manifest.kind not in {"dockerfile", "compose", "kubernetes", "terraform", "github-actions", "gitlab-ci", "nginx"} else "config")
            if dep.version:
                # 优先使用"主依赖"的版本号：vite 的版本比 @vitejs/plugin-react 的版本更可信。
                dep_key = catalog.normalize_name(dep.name)
                if spec is None:
                    score = 2
                elif dep_key == catalog.normalize_name(spec.name):
                    score = 2
                elif dep_key in {catalog.normalize_name(alias) for alias in spec.aliases}:
                    score = 1
                else:
                    score = 0
                # 只有"更可信"时才覆盖，同等可信则保留先出现的（例如 torch 会保留，
                # 不会被后面的 torchvision 覆盖）。
                if score > hit.version_score or not hit.version:
                    hit.version = dep.version
                    hit.version_score = score
            hit.add_evidence(dep.path, dep.line, dep.text, "依赖声明")
            if manifest.kind in {"dockerfile", "compose", "kubernetes", "terraform", "nginx", "github-actions", "gitlab-ci"}:
                hit.add_module(dep.path, dep.line, dep.text, "配置")

    # 3) import：找出每个文件用了什么
    if progress:
        progress("正在分析 import，定位使用各技术的模块…")
    for path, refs in imports.items():
        for ref in refs:
            spec = _match_import(ref.module)
            if spec is None:
                continue
            hit = get_hit(spec)
            hit.sources.add("import")
            if hit.confidence != "高":
                hit.confidence = "中"
            hit.add_evidence(path, ref.line, ref.text, "import")
            hit.add_module(path, ref.line, ref.text, "导入")

    # 4) 排序：分类顺序 -> 置信度 -> 模块数 -> 名字
    category_order = {name: index for index, name in enumerate(catalog.CATEGORIES)}
    confidence_order = {"高": 0, "中": 1, "低": 2}
    result = list(techs.values())
    result.sort(
        key=lambda hit: (
            category_order.get(hit.category, 99),
            confidence_order.get(hit.confidence, 9),
            -len(hit.modules),
            hit.name.lower(),
        )
    )
    return result, len(omitted_names)


def get_tech_by_name(snapshot: Snapshot, name: str) -> TechHit | None:
    """按名字查一项技术（大小写不敏感，也接受别名）。"""
    wanted = catalog.normalize_name(name)
    for tech in snapshot.techs:
        if catalog.normalize_name(tech.name) == wanted or tech.key == wanted:
            return tech
    spec = catalog.lookup(name)
    if spec is not None:
        for tech in snapshot.techs:
            if tech.key == spec.name.lower():
                return tech
    # 宽松一点：允许 "React.js" 匹配 "React"（要求至少 4 个字符，避免 Go 匹配到 Django）
    if len(wanted) >= 4:
        for tech in snapshot.techs:
            tech_key = catalog.normalize_name(tech.name)
            if len(tech_key) >= 4 and (wanted in tech_key or tech_key in wanted):
                return tech
    return None
