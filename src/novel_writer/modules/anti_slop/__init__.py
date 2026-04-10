"""Anti-Slop 模块 - 降 AI 率引擎.

核心差异化功能：检测并降低 AI 生成文本的检测率。
三阶段工作流：Prompt 预防 → 本地统计分析 → 定向改写。
"""

from __future__ import annotations

from novel_writer.core.module import Module, PageDef


class AntiSlopModule(Module):
    """降 AI 率引擎模块."""

    @property
    def name(self) -> str:
        return "anti_slop"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "检测并降低 AI 生成文本的 AI 检测率（对标朱雀AI检测）"

    def get_pages(self) -> list[PageDef]:
        from novel_writer.modules.anti_slop.ui import render_detection_page

        return [
            PageDef(
                title="AI 检测",
                icon="🔍",
                render=render_detection_page,
                order=50,
            )
        ]

    def on_startup(self) -> None:
        # 预加载词库
        from novel_writer.modules.anti_slop.dictionary import get_dictionary

        get_dictionary()


def create_module() -> AntiSlopModule:
    """工厂函数 - 被 ModuleRegistry 自动调用."""
    return AntiSlopModule()
