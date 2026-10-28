"""读取配置：这个项目用哪个大模型？

【给初学者：为什么需要这个文件？】
LangChain 的 Agent 本身不会"思考"，思考的是大模型（例如 DeepSeek、智谱 GLM）。
调用大模型需要两样东西：

    1. api_key   —— 相当于账号密码，证明"你有权限调用"
    2. base_url  —— 服务地址（门牌号），告诉程序去哪个网址发请求

这些东西绝对不能写死在代码里（会被上传到 GitHub 泄露），
所以统一放在项目根目录的 .env 文件里，由本文件读出来。

【本项目的兼容策略】
支持三种常见的 OpenAI 兼容接口：

    DEEPSEEK_API_KEY  -> https://api.deepseek.com          （默认模型 deepseek-chat）
    GLM_API_KEY       -> https://open.bigmodel.cn/api/paas/v4/（默认模型 glm-4.7）
    OPENAI_API_KEY    -> https://api.openai.com/v1         （默认模型 gpt-4o-mini）

只要填了其中一个就能跑。一个都没填也不会崩溃：
网页依然可以完成"规则扫描"，只是没有 AI 写的总结（报告里会明确标注）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录：config.py 在 repolens/ 子目录里，所以往上跳两级。
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 依次尝试加载两个 .env：
#   1. 项目自己的 .env（repolens/.env）
#   2. 上一级目录的 .env（方便复用你已有练习项目的密钥）
# override=False 表示"先加载的优先"，不会被后面的文件覆盖。
for env_file in (PROJECT_ROOT / ".env", PROJECT_ROOT.parent / ".env"):
    load_dotenv(env_file, override=False)

# .env.example 里的示例值。读到这些就当作"还没填"，避免拿假密钥去请求。
_PLACEHOLDERS = ("xxxx", "your-api-key", "your_api_key", "your-key", "在此填写", "填")


@dataclass
class ProviderSpec:
    """一家模型供应商的默认参数。"""

    provider: str
    label: str
    key_env: str
    model_env: str
    base_url_env: str
    default_model: str
    default_base_url: str
    default_temperature: float


PROVIDERS: dict[str, ProviderSpec] = {
    "deepseek": ProviderSpec(
        provider="deepseek",
        label="DeepSeek",
        key_env="DEEPSEEK_API_KEY",
        model_env="DEEPSEEK_MODEL",
        base_url_env="DEEPSEEK_BASE_URL",
        default_model="deepseek-chat",
        default_base_url="https://api.deepseek.com",
        default_temperature=0.3,
    ),
    "glm": ProviderSpec(
        provider="glm",
        label="智谱 GLM",
        key_env="GLM_API_KEY",
        model_env="GLM_MODEL",
        base_url_env="GLM_BASE_URL",
        default_model="glm-4.7",
        default_base_url="https://open.bigmodel.cn/api/paas/v4/",
        default_temperature=0.3,
    ),
    "openai": ProviderSpec(
        provider="openai",
        label="OpenAI",
        key_env="OPENAI_API_KEY",
        model_env="OPENAI_MODEL",
        base_url_env="OPENAI_BASE_URL",
        default_model="gpt-4o-mini",
        default_base_url="https://api.openai.com/v1",
        default_temperature=0.3,
    ),
}

AUTO_ORDER = ("deepseek", "glm", "openai")


def _read_text(env_name: str, default: str = "") -> str:
    """读一个文本型环境变量：没填或全是空白就返回默认值。"""
    value = os.getenv(env_name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _read_float(env_name: str, default: float) -> float:
    """读一个小数型环境变量；填得不对（比如写了 abc）就用默认值。"""
    value = _read_text(env_name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(word in lowered for word in _PLACEHOLDERS)


@dataclass
class ModelConfig:
    """本次运行要使用的模型配置。"""

    provider: str
    label: str
    model: str
    api_key: str
    base_url: str
    temperature: float
    timeout: float = 180.0
    max_retries: int = 1
    skipped: list[str] = field(default_factory=list)

    @property
    def available(self) -> bool:
        """有没有配置好密钥？没有的话项目会自动降级为"纯规则扫描"。"""
        return bool(self.api_key)

    @property
    def display_name(self) -> str:
        return f"{self.label} · {self.model}"


def load_model_config() -> ModelConfig:
    """决定用哪一家模型，并返回完整配置。

    选择规则：
      1. 如果 .env 里写了 MODEL_PROVIDER=glm，就优先用 glm；
      2. 否则按 DeepSeek -> GLM -> OpenAI 的顺序，找第一个填了密钥的；
      3. 都没有，返回 available=False 的配置（不抛异常）。
    """
    requested = _read_text("MODEL_PROVIDER", "auto").lower()
    order = list(AUTO_ORDER)
    if requested in PROVIDERS:
        order = [requested] + [name for name in AUTO_ORDER if name != requested]

    skipped: list[str] = []
    for provider_name in order:
        spec = PROVIDERS[provider_name]
        key = _read_text(spec.key_env)
        if not key or _is_placeholder(key):
            skipped.append(spec.label)
            continue

        return ModelConfig(
            provider=spec.provider,
            label=spec.label,
            model=_read_text(spec.model_env, spec.default_model),
            api_key=key,
            base_url=_read_text(spec.base_url_env, spec.default_base_url),
            temperature=_read_float("MODEL_TEMPERATURE", spec.default_temperature),
            timeout=_read_float("MODEL_TIMEOUT", 180.0),
            skipped=skipped,
        )

    spec = PROVIDERS["deepseek"]
    return ModelConfig(
        provider=spec.provider,
        label=spec.label,
        model=_read_text(spec.model_env, spec.default_model),
        api_key="",
        base_url=_read_text(spec.base_url_env, spec.default_base_url),
        temperature=0.3,
        skipped=skipped,
    )


# 其他可选配置 -------------------------------------------------------------

HOST = _read_text("REPOLENS_HOST", "127.0.0.1")
PORT = int(_read_text("REPOLENS_PORT", "8765"))

# 本地仓库路径的允许范围：留空表示"不限制"（项目默认，适合本地学习）。
# 如果想更安全，可以写成逗号分隔的目录，例如：
#   REPOLENS_ALLOWED_ROOTS=C:\Users\me\projects,D:\code
ALLOWED_LOCAL_ROOTS = [
    item.strip()
    for item in _read_text("REPOLENS_ALLOWED_ROOTS", "").split(",")
    if item.strip()
]

# GitHub 克隆的缓存目录和体积上限（MB）
DATA_DIR = PROJECT_ROOT / "data"
REPOS_DIR = DATA_DIR / "repos"
REPORTS_DIR = DATA_DIR / "reports"
DB_PATH = DATA_DIR / "repolens.db"
MAX_CLONE_MB = int(_read_text("REPOLENS_MAX_CLONE_MB", "300"))
CLONE_TIMEOUT_SECONDS = int(_read_text("REPOLENS_CLONE_TIMEOUT", "180"))
