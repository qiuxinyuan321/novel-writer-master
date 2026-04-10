"""生成引擎模块 - 场景生成 + 章节摘要 + 写作台."""

from novel_craft.core.module import Module, PageDef


class GenerationModule(Module):
    @property
    def name(self) -> str:
        return "generation"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "AI 场景生成引擎（大纲+记忆+anti-slop → 正文）"

    @property
    def dependencies(self) -> list[str]:
        return ["project", "bible", "outline", "anti_slop"]

    def get_pages(self) -> list[PageDef]:
        from novel_craft.modules.generation.ui import render_write_page
        return [PageDef(title="写作台", icon="✍️", render=render_write_page, order=40)]


def create_module() -> GenerationModule:
    return GenerationModule()
