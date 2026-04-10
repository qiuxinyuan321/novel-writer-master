"""模块系统 - 所有功能模块的基类和注册中心.

新增模块只需:
1. 在 modules/ 下创建目录，实现 Module 子类
2. 在 config.yaml 的 modules.enabled 中添加模块名
3. 无需修改任何已有代码
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class PageDef:
    """Streamlit 页面定义."""

    title: str  # 页面标题（显示在侧边栏）
    icon: str  # 图标 emoji
    render: Callable[[], None]  # 渲染函数
    order: int = 0  # 排序权重（越小越靠前）


class Module(ABC):
    """所有功能模块的基类.

    实现此接口即可注册为一个可插拔模块。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """模块唯一标识（用于配置和引用）."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """模块版本号."""
        ...

    @property
    def description(self) -> str:
        """模块描述（可选）."""
        return ""

    @property
    def dependencies(self) -> list[str]:
        """依赖的其他模块名（可选）."""
        return []

    def get_pages(self) -> list[PageDef]:
        """返回此模块提供的 Streamlit 页面列表（可选）."""
        return []

    def on_startup(self) -> None:
        """应用启动时调用（可选）."""
        pass

    def on_shutdown(self) -> None:
        """应用关闭时调用（可选）."""
        pass


class ModuleRegistry:
    """模块注册中心 - 自动发现和加载模块."""

    def __init__(self) -> None:
        self._modules: dict[str, Module] = {}

    def register(self, module: Module) -> None:
        """注册一个模块."""
        if module.name in self._modules:
            logger.warning(f"模块 {module.name} 已注册，跳过重复注册")
            return
        self._modules[module.name] = module
        logger.info(f"已注册模块: {module.name} v{module.version}")

    def get(self, name: str) -> Module | None:
        """按名称获取模块."""
        return self._modules.get(name)

    def list_modules(self) -> list[Module]:
        """列出所有已注册模块."""
        return list(self._modules.values())

    def get_all_pages(self) -> list[PageDef]:
        """收集所有模块的页面定义，按 order 排序."""
        pages: list[PageDef] = []
        for module in self._modules.values():
            pages.extend(module.get_pages())
        return sorted(pages, key=lambda p: p.order)

    def startup_all(self) -> None:
        """启动所有已注册模块."""
        for module in self._modules.values():
            try:
                module.on_startup()
            except Exception as e:
                logger.error(f"模块 {module.name} 启动失败: {e}")

    def shutdown_all(self) -> None:
        """关闭所有已注册模块."""
        for module in self._modules.values():
            try:
                module.on_shutdown()
            except Exception as e:
                logger.error(f"模块 {module.name} 关闭失败: {e}")

    def load_enabled_modules(self, enabled: list[str]) -> None:
        """根据配置加载启用的模块.

        自动从 novel_craft.modules.{name} 导入并注册。
        每个模块包的 __init__.py 需要提供 create_module() 工厂函数。
        """
        for name in enabled:
            if name in self._modules:
                continue
            try:
                mod = importlib.import_module(f"novel_craft.modules.{name}")
                if hasattr(mod, "create_module"):
                    module_instance = mod.create_module()
                    self.register(module_instance)
                else:
                    logger.warning(f"模块 {name} 缺少 create_module() 工厂函数")
            except ImportError as e:
                logger.warning(f"无法加载模块 {name}: {e}")
            except Exception as e:
                logger.error(f"加载模块 {name} 时出错: {e}")


# 全局注册中心单例
registry = ModuleRegistry()
