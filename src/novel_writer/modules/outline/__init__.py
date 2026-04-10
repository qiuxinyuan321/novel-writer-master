"""大纲模块 - 分层大纲 + 检查点."""

from novel_writer.core.module import Module, PageDef


class OutlineModule(Module):
    @property
    def name(self) -> str:
        return "outline"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "分层大纲管理（全书→卷→章→场景）+ 检查点约束"

    @property
    def dependencies(self) -> list[str]:
        return ["project"]

    def get_pages(self) -> list[PageDef]:
        from novel_writer.modules.outline.ui import render_outline_page
        return [PageDef(title="大纲", icon="🗂️", render=render_outline_page, order=30)]


def create_module() -> OutlineModule:
    return OutlineModule()
