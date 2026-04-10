"""配置管理 - 加载 config.yaml + 环境变量覆盖."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProviderConfig:
    """单个 LLM Provider 配置."""

    base_url: str
    api_key: str
    model: str
    max_tokens: int = 4096


@dataclass
class LLMConfig:
    """LLM 总配置."""

    default_provider: str = "claude"
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    routing: dict[str, str] = field(default_factory=dict)


@dataclass
class AntiSlopConfig:
    """Anti-Slop 引擎配置."""

    weights: dict[str, float] = field(
        default_factory=lambda: {
            "blacklist_density": 0.30,
            "ttr": 0.25,
            "sentence_variance": 0.20,
            "structure_pattern": 0.15,
            "repetition": 0.10,
        }
    )
    thresholds: dict[str, float] = field(
        default_factory=lambda: {"low": 0.3, "medium": 0.6, "high": 0.6}
    )
    max_rewrite_rounds: int = 2


@dataclass
class AppConfig:
    """应用总配置."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    modules_enabled: list[str] = field(
        default_factory=lambda: ["anti_slop", "project", "bible", "outline", "generation"]
    )
    anti_slop: AntiSlopConfig = field(default_factory=AntiSlopConfig)
    db_path: str = "data/novel_writer.db"
    chroma_path: str = "data/chroma"
    project_root: Path = field(default_factory=lambda: Path.cwd())


def _parse_providers(raw: dict[str, Any]) -> dict[str, ProviderConfig]:
    """解析 providers 配置."""
    result = {}
    for name, cfg in raw.items():
        if not isinstance(cfg, dict):
            continue
        # 环境变量覆盖: NOVELCRAFT_LLM_{NAME}_API_KEY
        env_key = f"NOVELCRAFT_LLM_{name.upper()}_API_KEY"
        api_key = os.environ.get(env_key, cfg.get("api_key", ""))
        result[name] = ProviderConfig(
            base_url=cfg.get("base_url", ""),
            api_key=api_key,
            model=cfg.get("model", ""),
            max_tokens=cfg.get("max_tokens", 4096),
        )
    return result


def load_config(config_path: str | Path | None = None) -> AppConfig:
    """加载配置文件，支持 config.yaml 和环境变量覆盖."""
    if config_path is None:
        # 按优先级查找配置文件
        for candidate in ["config.yaml", "config.yml", "config.example.yaml"]:
            p = Path(candidate)
            if p.exists():
                config_path = p
                break

    raw: dict[str, Any] = {}
    if config_path and Path(config_path).exists():
        with open(config_path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    # 解析 LLM 配置
    llm_raw = raw.get("llm", {})
    llm_config = LLMConfig(
        default_provider=llm_raw.get("default_provider", "claude"),
        providers=_parse_providers(llm_raw.get("providers", {})),
        routing=llm_raw.get("routing", {}),
    )

    # 解析模块列表
    modules_raw = raw.get("modules", {})
    modules_enabled = modules_raw.get("enabled", ["anti_slop"])

    # 解析 anti-slop 配置
    as_raw = raw.get("anti_slop", {})
    anti_slop = AntiSlopConfig(
        weights=as_raw.get("weights", AntiSlopConfig().weights),
        thresholds=as_raw.get("thresholds", AntiSlopConfig().thresholds),
        max_rewrite_rounds=as_raw.get("max_rewrite_rounds", 2),
    )

    # 数据目录
    data_raw = raw.get("data", {})

    return AppConfig(
        llm=llm_config,
        modules_enabled=modules_enabled,
        anti_slop=anti_slop,
        db_path=data_raw.get("db_path", "data/novel_writer.db"),
        chroma_path=data_raw.get("chroma_path", "data/chroma"),
    )


# 全局单例
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """获取全局配置单例."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reset_config() -> None:
    """重置配置（测试用）."""
    global _config
    _config = None
