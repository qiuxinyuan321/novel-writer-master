"""项目管理模块."""

from novel_craft.core.module import Module, PageDef


class ProjectModule(Module):
    @property
    def name(self) -> str:
        return "project"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "小说项目创建与管理"

    def get_pages(self) -> list[PageDef]:
        from novel_craft.modules.project.ui import render_projects_page
        return [PageDef(title="项目管理", icon="📚", render=render_projects_page, order=10)]

    def on_startup(self) -> None:
        from novel_craft.models import Novel  # 确保模型注册
        from novel_craft.db import init_db
        init_db()


def create_module() -> ProjectModule:
    return ProjectModule()
