"""导出模块 - 合并章节为 TXT/DOCX."""

from novel_craft.core.module import Module, PageDef


class ExportModule(Module):
    @property
    def name(self) -> str:
        return "export"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "导出小说为 TXT/DOCX 文件"

    @property
    def dependencies(self) -> list[str]:
        return ["project"]

    def get_pages(self) -> list[PageDef]:
        from novel_craft.modules.export.ui import render_export_page
        return [PageDef(title="导出", icon="📥", render=render_export_page, order=70)]


def create_module() -> ExportModule:
    return ExportModule()
