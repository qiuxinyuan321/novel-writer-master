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

    def get_pages(self) -> list[PageDef]:
        return []  # 暂不提供独立页面，集成在写作台中


def create_module() -> ConsistencyModule:
    return ConsistencyModule()
