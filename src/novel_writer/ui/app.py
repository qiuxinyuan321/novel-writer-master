"""小说伴写大师 Streamlit 主应用入口.

自动加载所有已启用模块注册的页面。
启动: streamlit run src/novel_writer/ui/app.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st

# 确保项目根目录在 Python 路径中
_project_root = Path(__file__).parent.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

from novel_writer.config import get_config
from novel_writer.core.module import registry

logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def init_app() -> None:
    """初始化应用（只在首次运行时执行）."""
    if "initialized" not in st.session_state:
        config = get_config()
        registry.load_enabled_modules(config.modules_enabled)
        registry.startup_all()
        st.session_state.initialized = True
        logger.info(
            f"小说伴写大师 已初始化，已加载模块: "
            f"{[m.name for m in registry.list_modules()]}"
        )


def main() -> None:
    """主入口."""
    st.set_page_config(
        page_title="小说伴写大师",
        page_icon="✍️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_app()

    # 侧边栏
    with st.sidebar:
        st.title("✍️ 小说伴写大师")
        st.caption("AI 辅助小说写作 · 内置降 AI 率引擎")
        st.divider()

        # 收集所有模块页面
        pages = registry.get_all_pages()
        if not pages:
            st.warning("未加载任何模块页面")
            return

        # 页面导航
        page_titles = [f"{p.icon} {p.title}" for p in pages]

        # 默认选中第一个页面
        if "current_page" not in st.session_state:
            st.session_state.current_page = 0

        selected = st.radio(
            "导航",
            page_titles,
            index=st.session_state.current_page,
            label_visibility="collapsed",
        )

        # 更新当前页面索引
        if selected:
            st.session_state.current_page = page_titles.index(selected)

        st.divider()

        # 模块信息
        with st.expander("已加载模块"):
            for m in registry.list_modules():
                st.text(f"  {m.name} v{m.version}")

    # 渲染当前选中的页面
    current_idx = st.session_state.current_page
    if 0 <= current_idx < len(pages):
        pages[current_idx].render()


if __name__ == "__main__":
    main()
