"""核心框架 - Module 注册、事件总线、生命周期钩子."""

from novel_craft.core.events import EventBus, event_bus
from novel_craft.core.module import Module, ModuleRegistry, registry

__all__ = ["Module", "ModuleRegistry", "registry", "EventBus", "event_bus"]
