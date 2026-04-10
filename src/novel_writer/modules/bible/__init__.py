"""Story Bible 模块 - 角色/世界观/伏笔管理."""

from novel_writer.core.module import Module, PageDef


class BibleModule(Module):
    @property
    def name(self) -> str:
        return "bible"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "角色档案、世界观设定、伏笔管理"

    @property
    def dependencies(self) -> list[str]:
        return ["project"]

    def get_pages(self) -> list[PageDef]:
        from novel_writer.modules.bible.ui import render_bible_page
        return [PageDef(title="Story Bible", icon="📖", render=render_bible_page, order=20)]


def create_module() -> BibleModule:
    return BibleModule()
