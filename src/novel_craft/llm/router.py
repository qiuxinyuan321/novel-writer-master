"""模型路由器 - 根据任务类型选择 Provider.

配置示例 (config.yaml):
  llm:
    default_provider: claude
    routing:
      generation: claude       # 正文生成用强模型
      rewrite: claude          # 改写也用强模型
      summary: deepseek        # 摘要用便宜模型
"""

from __future__ import annotations

import logging

from novel_craft.config import AppConfig, get_config
from novel_craft.llm.client import LLMClient

logger = logging.getLogger(__name__)


class LLMRouter:
    """模型路由器 - 管理多个 Provider 并按任务分发."""

    def __init__(self, config: AppConfig) -> None:
        self._clients: dict[str, LLMClient] = {}
        self._default_provider = config.llm.default_provider
        self._routing = config.llm.routing

        # 初始化所有已配置的 Provider
        for name, provider_config in config.llm.providers.items():
            if not provider_config.base_url or not provider_config.api_key:
                logger.debug(f"Provider {name} 缺少配置，跳过")
                continue
            self._clients[name] = LLMClient(provider_config, provider_name=name)
            logger.info(f"已初始化 LLM Provider: {name} ({provider_config.model})")

    def get_client(self, task: str = "default") -> LLMClient:
        """根据任务类型获取对应的 LLM 客户端.

        Args:
            task: 任务类型，如 "generation", "rewrite", "summary" 等。
                  匹配 config.yaml 中 llm.routing 的 key。

        Returns:
            对应的 LLMClient 实例。

        Raises:
            ValueError: 没有可用的 Provider。
        """
        # 查找任务对应的 Provider
        provider_name = self._routing.get(task, self._default_provider)

        # 如果指定的 Provider 不可用，回退到默认
        if provider_name not in self._clients:
            if self._default_provider in self._clients:
                provider_name = self._default_provider
            elif self._clients:
                provider_name = next(iter(self._clients))
            else:
                raise ValueError("没有可用的 LLM Provider，请检查 config.yaml")

        return self._clients[provider_name]

    @property
    def available_providers(self) -> list[str]:
        """列出所有可用的 Provider 名称."""
        return list(self._clients.keys())

    def has_provider(self, name: str) -> bool:
        """检查指定 Provider 是否可用."""
        return name in self._clients


# 全局单例
_router: LLMRouter | None = None


def get_router() -> LLMRouter:
    """获取全局路由器单例."""
    global _router
    if _router is None:
        _router = LLMRouter(get_config())
    return _router


def reset_router() -> None:
    """重置路由器（测试用）."""
    global _router
    _router = None
