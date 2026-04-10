"""一致性检查模块（可选）."""

from novel_craft.core.module import Module, PageDef


class ConsistencyModule(Module):
    @property
    def name(self) -> str:
        return "consistency"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "LLM 驱动的角色行为/世界观/时间线一致性检查"

    @property
    def dependencies(self) -> list[str]:
        return ["project", "bible"]

    def get_pages(self) -> list[PageDef]:
        from novel_craft.modules.consistency.ui import render_consistency_page
        return [PageDef(title="一致性检查", icon="🔎", render=render_consistency_page, order=55)]


def create_module() -> ConsistencyModule:
    return ConsistencyModule()
