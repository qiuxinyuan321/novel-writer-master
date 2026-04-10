"""仪表盘模块 - 进度统计 + 情绪节奏图."""

from novel_craft.core.module import Module, PageDef


class DashboardModule(Module):
    @property
    def name(self) -> str:
        return "dashboard"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "写作进度统计、情绪节奏图、AI风险分布"

    @property
    def dependencies(self) -> list[str]:
        return ["project"]

    def get_pages(self) -> list[PageDef]:
        from novel_craft.modules.dashboard.ui import render_dashboard_page
        return [PageDef(title="仪表盘", icon="📊", render=render_dashboard_page, order=60)]


def create_module() -> DashboardModule:
    return DashboardModule()
