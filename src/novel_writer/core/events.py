"""事件总线 - 模块间松耦合通信.

模块通过事件总线通信，避免硬依赖。
示例:
    # 发布事件
    event_bus.emit("scene_generated", scene_id="abc", content="...")

    # 订阅事件
    @event_bus.on("scene_generated")
    def on_scene_generated(scene_id: str, content: str):
        # anti_slop 模块自动评分
        score = analyzer.analyze(content)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[..., Any]


class EventBus:
    """简单的同步事件总线."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event_name: str) -> Callable[[EventHandler], EventHandler]:
        """装饰器：订阅事件."""

        def decorator(handler: EventHandler) -> EventHandler:
            self._handlers[event_name].append(handler)
            return handler

        return decorator

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """订阅事件."""
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """取消订阅."""
        if event_name in self._handlers:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name] if h is not handler
            ]

    def emit(self, event_name: str, **kwargs: Any) -> list[Any]:
        """发布事件，返回所有 handler 的结果列表."""
        results = []
        for handler in self._handlers.get(event_name, []):
            try:
                result = handler(**kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"事件 {event_name} 的 handler {handler.__name__} 出错: {e}")
        return results

    def clear(self) -> None:
        """清除所有订阅（测试用）."""
        self._handlers.clear()


# 全局事件总线单例
event_bus = EventBus()
