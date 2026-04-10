"""统一 LLM 客户端 - 所有 Provider 通过 OpenAI 兼容接口访问.

接入新 LLM 只需在 config.yaml 中添加 base_url + api_key + model。
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from novel_writer.config import ProviderConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """统一 LLM 客户端.

    所有 Provider（Claude/OpenAI/DeepSeek/Ollama/自定义）
    通过 OpenAI Chat Completions 兼容接口访问。
    """

    def __init__(self, config: ProviderConfig, provider_name: str = "unknown") -> None:
        self.provider_name = provider_name
        self.model = config.model
        self.max_tokens = config.max_tokens
        self._client = AsyncOpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> str:
        """发送聊天请求，返回完整响应文本."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or self.max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """发送流式聊天请求，逐 chunk 返回文本."""
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens or self.max_tokens,
            stream=True,
            **kwargs,
        )
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def test_connection(self) -> tuple[bool, str]:
        """测试连接是否可用，返回 (成功, 消息)."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )
            model_used = response.model or self.model
            return True, f"连接成功 (模型: {model_used})"
        except Exception as e:
            return False, f"连接失败: {e}"
