"""大纲 Streamlit UI - 分层大纲编辑器."""

from __future__ import annotations

import streamlit as st

from novel_craft.modules.outline.service import (
    create_outline,
    delete_outline,
    get_outline_tree,
    list_outlines,
    update_outline,
)

EMOTIONS = ["紧张", "舒缓", "高潮", "悲伤", "喜悦", "悬疑", "恐怖", "温馨", "搞笑", "热血", "平淡"]
LEVELS = {"chapter": "章", "scene": "场景"}


def _get_novel_id() -> str | None:
    return st.session_state.get("current_novel_id")


def render_outline_page() -> None:
    novel_id = _get_novel_id()
    if not novel_id:
        st.warning("请先在「项目管理」中打开一个小说项目")
        return

    st.header(f"🗂️ 大纲 - {st.session_state.get('current_novel_title', '')}")

    tab_tree, tab_add = st.tabs(["📋 大纲结构", "➕ 添加节点"])

    with tab_add:
        _render_add_outline(novel_id)

    with tab_tree:
        _render_outline_tree(novel_id)


def _render_add_outline(novel_id: str) -> None:
    """添加大纲节点."""
    with st.form("add_outline"):
        level = st.selectbox("层级", ["chapter", "scene"], format_func=lambda x: LEVELS[x])

        # 如果是场景级，需要选择父章节
        parent_id = None
        if level == "scene":
            chapters = list_outlines(novel_id, parent_id=None)
            chapter_outlines = [o for o in chapters if o.level == "chapter"]
            if chapter_outlines:
                parent_options = {o.id: f"第{o.order_index+1}章: {o.title}" for o in chapter_outlines}
                parent_id = st.selectbox("所属章节", list(parent_options.keys()),
                                         format_func=lambda x: parent_options[x])
            else:
                st.warning("请先添加章级大纲")

        title = st.text_input("标题", placeholder="如：初入江湖 / 密室对峙")
        narrative_goal = st.text_area("叙事目标", height=80,
                                      placeholder="本章/场景需要完成的叙事任务...")
        emotion = st.selectbox("目标情绪", EMOTIONS)

        # 检查点
        st.markdown("**检查点（必须达成的叙事里程碑）:**")
        cp_text = st.text_area("每行一个检查点", height=60,
                               placeholder="角色A必须到达城市B\n伏笔X必须被揭示")

        content = st.text_area("大纲正文", height=100, placeholder="详细的章节/场景描述...")

        order = st.number_input("排序序号", min_value=0, value=0)

        if st.form_submit_button("添加", type="primary") and title.strip():
            checkpoints = []
            if cp_text.strip():
                for line in cp_text.strip().split("\n"):
                    if line.strip():
                        checkpoints.append({
                            "description": line.strip(),
                            "is_mandatory": True,
                            "verified": False,
                        })

            create_outline(
                novel_id=novel_id,
                level=level,
                title=title.strip(),
                parent_id=parent_id,
                narrative_goal=narrative_goal.strip(),
                emotion_target=emotion,
                checkpoints=checkpoints,
                content_preview=content.strip(),
                order_index=order,
            )
            st.success(f"已添加: {title}")
            st.rerun()


def _render_outline_tree(novel_id: str) -> None:
    """渲染大纲树."""
    tree = get_outline_tree(novel_id)
    if not tree:
        st.info("还没有大纲，点击「添加节点」开始规划")
        return

    for node in tree:
        _render_node(node, depth=0)


def _render_node(node: dict, depth: int) -> None:
    """递归渲染大纲节点."""
    indent = "　" * depth
    level_icon = {"chapter": "📑", "scene": "🎬"}.get(node["level"], "📄")
    level_label = LEVELS.get(node["level"], node["level"])

    # 检查点状态
    cps = node.get("checkpoints", [])
    cp_done = sum(1 for cp in cps if cp.get("verified"))
    cp_total = len(cps)
    cp_info = f" [{cp_done}/{cp_total}✓]" if cp_total > 0 else ""

    emotion = f" 🎭{node['emotion_target']}" if node.get("emotion_target") else ""

    with st.expander(
        f"{indent}{level_icon} {level_label}: {node['title']}{emotion}{cp_info}",
        expanded=depth == 0,
    ):
        if node.get("narrative_goal"):
            st.markdown(f"**叙事目标:** {node['narrative_goal']}")

        # 检查点列表
        if cps:
            st.markdown("**检查点:**")
            for cp in cps:
                check = "✅" if cp.get("verified") else "⬜"
                mandatory = " (必须)" if cp.get("is_mandatory") else ""
                st.markdown(f"  {check} {cp['description']}{mandatory}")

        if node.get("content_preview"):
            st.caption(node["content_preview"][:200])

        # 操作按钮
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("删除", key=f"del_outline_{node['id']}", type="secondary"):
                delete_outline(node["id"])
                st.rerun()

    # 递归渲染子节点
    for child in node.get("children", []):
        _render_node(child, depth + 1)
