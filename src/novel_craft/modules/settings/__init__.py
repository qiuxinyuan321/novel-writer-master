"""设置模块 - LLM Provider 配置 + 系统信息."""

from novel_craft.core.module import Module, PageDef


class SettingsModule(Module):
    @property
    def name(self) -> str:
        return "settings"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def description(self) -> str:
        return "LLM Provider 配置、连接测试、系统信息"

    def get_pages(self) -> list[PageDef]:
        from novel_craft.modules.settings.ui import render_settings_page
        return [PageDef(title="设置", icon="⚙️", render=render_settings_page, order=90)]


def create_module() -> SettingsModule:
    return SettingsModule()
