"""LLM 统一接入层 - 多 Provider 支持."""

from novel_craft.llm.client import LLMClient
from novel_craft.llm.router import LLMRouter, get_router

__all__ = ["LLMClient", "LLMRouter", "get_router"]
