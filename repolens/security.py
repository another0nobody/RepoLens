"""敏感信息脱敏：避免把仓库里的密钥原样送给大模型。

【给初学者：为什么 Agent 项目要特别注意这个？】
Agent 会读文件。很多项目把数据库密码、API Key 写在 .env、config.py 里。
如果把这些内容原样塞进提示词发给模型服务商，就相当于把密钥"寄"了出去。

本文件做两件事：
    1. 对要发给模型/展示在网页上的文本做正则替换（sk-xxx、password=xxx 等）；
    2. 明确禁止读取 .env、私钥等敏感文件（读取工具会先检查）。
"""

from __future__ import annotations

import re

# (正则, 替换文本)。替换文本里的 \1 表示"保留第一组，也就是字段名"。
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
        "[私钥内容已隐藏]",
    ),
    (re.compile(r"\b(sk-[A-Za-z0-9_\-]{10,})\b"), "sk-***已隐藏***"),
    # 智谱 GLM 的 Key 形如 32 位十六进制 + "." + 8 位以上字母数字
    (re.compile(r"\b([0-9a-f]{32}\.[A-Za-z0-9]{8,})\b"), "***GLM Key 已隐藏***"),
    (
        re.compile(r"(?i)\b(api[_-]?key|secret[_-]?key|access[_-]?key)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-./+]{8,})"),
        r"\1=***已隐藏***",
    ),
    (
        re.compile(r"(?i)\b(password|passwd|pwd)\b\s*[:=]\s*['\"]?([^'\"\s,;]{4,})"),
        r"\1=***已隐藏***",
    ),
    (
        re.compile(r"(?i)\b(token|authorization)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-.]{12,})"),
        r"\1=***已隐藏***",
    ),
    (
        re.compile(r"(?i)\b(secret)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-./+]{8,})"),
        r"\1=***已隐藏***",
    ),
    (
        re.compile(r"(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://([^:\s/]+):([^@\s]+)@"),
        r"\1://\2:***已隐藏***@",
    ),
]

# 这些文件名/后缀默认不读取正文，防止一不小心把密钥读出来。
_SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "credentials",
    "credentials.json",
    "secrets.yml",
    "secrets.yaml",
}
_SENSITIVE_SUFFIXES = {".pem", ".key", ".pfx", ".p12", ".jks", ".keystore"}


def mask_secrets(text: str) -> tuple[str, int]:
    """把文本里的疑似密钥替换成占位符，返回 (脱敏后文本, 命中次数)。"""
    if not text:
        return text, 0
    masked = text
    hits = 0
    for pattern, replacement in _PATTERNS:
        masked, count = pattern.subn(replacement, masked)
        hits += count
    return masked, hits


def is_sensitive_path(path: str) -> bool:
    """判断路径是不是"不该读内容"的敏感文件。"""
    lowered = path.replace("\\", "/").lower()
    name = lowered.rsplit("/", 1)[-1]
    if name in _SENSITIVE_NAMES:
        return True
    if name.startswith(".env.") and name not in {".env.example", ".env.sample", ".env.template"}:
        return True
    if any(name.endswith(suffix) for suffix in _SENSITIVE_SUFFIXES):
        return True
    return False
